# Import PyObjC here. This is because the first import of PyObjC *must* be
# in the main thread. Otherwise, the NSAutoreleasePool created automatically
# by PyObjC on the first import would be released at exit by the main thread
# which would crash (because it was created in a different thread).
# http://pyobjc.sourceforge.net/documentation/pyobjc-core/intro.html
import objc

from collections import deque
from threading import Condition, Thread, currentThread

class OnRequestQueue:
	class QueueEnd:
		def __init__(self):
			self.q = deque()
			self.cond = Condition()
			self.cancel = False
		def setCancel(self):
			with self.cond:
				self.cancel = True
				self.cond.notify()
	def __init__(self):
		self.queues = set()
	def put(self, item):
		for q in self.queues:
			with q.cond:
				if q.cancel: continue
				q.q.append(item)
				q.cond.notify()
	def cancelAll(self):
		for q in list(self.queues):
			q.setCancel()
	def read(self):
		q = self.QueueEnd()
		thread = currentThread()
		thread.waitQueue = q
		if thread.cancel:
			# This is to avoid a small race condition for the case
			# that the thread which wants to join+cancel us was faster
			# and didn't got the waitQueue. In that case, it would
			# have set the cancel already to True.
			return
		self.queues.add(q)
		while True:
			with q.cond:
				l = list(q.q)
				q.q.clear()
				cancel = q.cancel
				if not l and not cancel:
					q.cond.wait()
			for item in l:
				yield item
			if cancel: break
		self.queues.remove(q)

class EventCallback:
	def __init__(self, targetQueue, name=None):
		self.targetQueue = targetQueue
		self.name = name
	def __call__(self, *args, **kwargs):
		self.targetQueue.put((self, args, kwargs))
	def __repr__(self):
		return "<EventCallback %s>" % self.name

class initBy(object):
	def __init__(self, initFunc):
		self.initFunc = initFunc
	def load(self, inst):
		if not hasattr(self, "value"):
			self.value = self.initFunc(inst)
	def __get__(self, inst, type=None):
		self.load(inst)
		if hasattr(self.value, "__get__"):
			return self.value.__get__(inst, type)
		return self.value
	def __set__(self, inst, value):
		self.load(inst)
		if hasattr(self.value, "__set__"):
			return self.value.__set__(inst, value)
		self.value = value
		
class oneOf(object):
	def __init__(self, *consts):
		assert len(consts) > 0
		self.consts = consts
		self.value = consts[0]
	def __get__(self, inst, type=None):
		return self
	def __set__(self, inst, value):
		assert value in self.consts
		self.value = value



def formatTime(t):
	if t is None: return "?"
	mins = long(t // 60)
	t -= mins * 60
	hours = mins // 60
	mins -= hours * 60
	if hours: return "%02i:%02i:%02.0f" % (hours,mins,t)
	return "%02i:%02.0f" % (mins,t)

def doAsync(f, name=None):
	from threading import Thread
	if name is None: name = repr(f)
	t = Thread(target = f, name = name)
	t.start()


def betterRepr(o):
	# the main difference: this one is deterministic
	# the orig dict.__repr__ has the order undefined.
	if isinstance(o, list):
		return "[\n" + "".join(map(lambda v: betterRepr(v) + ",\n", o)) + "]"
	if isinstance(o, deque):
		return "deque([\n" + "".join(map(lambda v: betterRepr(v) + ",\n", o)) + "])"
	if isinstance(o, tuple):
		return "(" + ", ".join(map(betterRepr, o)) + ")"
	if isinstance(o, dict):
		return "{\n" + "".join(map(lambda (k,v): betterRepr(k) + ": " + betterRepr(v) + ",\n", sorted(o.iteritems()))) + "}"
	# fallback
	return repr(o)

def ObjectProxy(lazyLoader, custom_attribs={}, baseType=object):
	class Value: pass
	obj = Value()
	def load():
		if not hasattr(obj, "value"):
			obj.value = lazyLoader()
	def obj_getattr(self, key):
		load()
		return getattr(obj.value, key)
	def obj_setattr(self, key, value):
		load()
		return setattr(obj.value, key, value)
	def obj_desc_get(self, inst, type=None):
		if inst is None:
			load()
			return obj.value
		return self
	def obj_desc_set(self, inst, value):
		if hasattr(value, "__get__"):
			# In case the value is itself some sort of ObjectProxy, try to get its
			# underlying object and use our proxy instead.
			obj.value = value.__get__(None)
		else:
			obj.value = value
	attribs = custom_attribs.copy()
	attribs.update({
		"__getattr__": obj_getattr,
		"__setattr__": obj_setattr,
		"__get__": obj_desc_get,
		"__set__": obj_desc_set,
		})
	LazyObject = type("LazyObject", (object,baseType), attribs)
	return LazyObject()

def PersistentObject(baseType, filename, persistentRepr = False):
	def load():
		import appinfo
		try:
			f = open(appinfo.userdir + "/" + filename)
		except IOError: # e.g. file-not-found. that's ok
			return baseType()

		# some common types
		g = {baseType.__name__: baseType} # the baseType itself
		g.update(globals()) # all what we have here
		if baseType.__module__:
			# the module of the basetype
			import sys
			m = sys.modules[baseType.__module__]
			g.update([(varname,getattr(m,varname)) for varname in dir(m)])
		obj = eval(f.read(), g)
		assert isinstance(obj, baseType)
		return obj
	def save(obj):
		s = betterRepr(obj.__get__(None))
		import appinfo
		f = open(appinfo.userdir + "/" + filename, "w")
		f.write(s)
		f.write("\n")
		f.close()
	def obj_repr(obj):
		if persistentRepr:
			return "PersistentObject(%s, %r)" % (baseType.__name__, filename)
		return betterRepr(obj.__get__(None))
	def obj_del(obj):
		save(obj)
	return ObjectProxy(load, baseType=baseType,
		custom_attribs={
			"save": save,
			"__repr__": obj_repr,
			"__del__": obj_del,
			})


class DictObj(dict):
	def __getattr__(self, item): return self[item]
	def __setattr__(self, key, value): self[key] = value


import better_exchook

class Module:
	def __init__(self, name):
		self.name = name
		self.thread = None
		self.module = None
	@property
	def mainFuncName(self): return self.name + "Main"
	@property
	def moduleName(self): return self.name
	def start(self):
		self.thread = Thread(target = self.threadMain, name = self.name + " main")
		self.thread.waitQueue = None
		self.thread.cancel = False
		self.thread.reload = False
		self.thread.start()
	def threadMain(self):
		better_exchook.install()
		thread = currentThread()
		while True:
			if self.mainFuncName in globals():
				mainFunc = globals()[self.mainFuncName]
			else:
				if self.module:
					reload(self.module)
				else:
					self.module = __import__(self.moduleName)
				mainFunc = getattr(self.module, self.mainFuncName)
			mainFunc()
			if not thread.reload: break
			thread.cancel = False
			thread.reload = False
			thread.waitQueue = None
	def stop(self, join=True):
		self.thread.cancel = True
		if self.thread.waitQueue:
			self.thread.waitQueue.setCancel()
		if join:
			self.thread.join()
	def reload(self):
		if self.thread and self.thread.isAlive():
			self.thread.reload = True
			self.stop(join=False)
		else:
			self.start()
