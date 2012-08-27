# Import PyObjC here. This is because the first import of PyObjC *must* be
# in the main thread. Otherwise, the NSAutoreleasePool created automatically
# by PyObjC on the first import would be released at exit by the main thread
# which would crash (because it was created in a different thread).
# http://pyobjc.sourceforge.net/documentation/pyobjc-core/intro.html
import objc

from collections import deque
from threading import Condition
class OnRequestQueue:
	class QueueEnd:
		def __init__(self):
			self.q = deque()
			self.cond = Condition()
			self.cancel = False
	def __init__(self):
		self.queues = set()
	def put(self, item):
		for q in self.queues:
			with q.cond:
				if q.cancel: continue
				q.q.append(item)
				q.cond.notify()
	def cancelAll(self):
		for q in self.queues:
			with q.cond:
				q.cancel = True
				q.cond.notify()
		self.queues.clear()
	def read(self):
		q = self.QueueEnd()
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

class EventCallback:
	def __init__(self, targetQueue, name=None):
		self.targetQueue = targetQueue
		self.name = name
	def __call__(self, *args, **kwargs):
		self.targetQueue.put((self, args, kwargs))
	def __repr__(self):
		return "<EventCallback %s>" % self.name

class initBy(property):
	def __init__(self, initFunc):
		property.__init__(self, fget = self.fget)
		self.initFunc = initFunc
	def fget(self, inst):
		if hasattr(self, "value"): return self.value
		self.value = self.initFunc(inst)
		return self.value

class oneOf(property):
	def __init__(self, *consts):
		property.__init__(self, fget = self.fget, fset = self.fset)
		assert len(consts) > 0
		self.consts = consts
		self.value = consts[0]
	def fget(self, inst):
		return self
	def fset(self, inst, value):
		assert value in self.consts
		self.value = value


def setTtyNoncanonical(fd, timeout=0):
	import termios
	old = termios.tcgetattr(fd)
	new = termios.tcgetattr(fd)
	new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
	# http://www.unixguide.net/unix/programming/3.6.2.shtml
	#new[6] [termios.VMIN] = 1
	#new[6] [termios.VTIME] = 0
	new[6] [termios.VMIN] = 0 if timeout > 0 else 1
	timeout *= 10 # 10ths of second
	if timeout > 0 and timeout < 1: timeout = 1
	new[6] [termios.VTIME] = timeout
		
	termios.tcsetattr(fd, termios.TCSANOW, new)
	termios.tcsendbreak(fd,0)

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
		return "[" + ", ".join(map(betterRepr, o)) + "]"
	if isinstance(o, tuple):
		return "(" + ", ".join(map(betterRepr, o)) + ")"
	if isinstance(o, dict):
		return "{\n" + "".join(map(lambda (k,v): betterRepr(k) + ": " + betterRepr(v) + ",\n", sorted(o.iteritems()))) + "}"
	# fallback
	return repr(o)

def ObjectProxy(lazyLoader, custom_attribs={}, baseType=object, delHook=None, getattrHook=getattr, setattrHook=setattr):
	class Value: pass
	obj = Value()
	def load():
		if not hasattr(obj, "value"):
			obj.value = lazyLoader()
	def obj_getattr(self, key):
		load()
		if key in custom_attribs:
			value = custom_attribs[key]
			if hasattr(value, "__get__"):
				value = value.__get__(self, type(self))
			return value
		return getattr(obj.value, key)
	def obj_setattr(self, key, value):
		load()
		return setattr(obj.value, key, value)
	def obj_del(self):
		if delHook: delHook(self)
	attribs = {"__getattr__": obj_getattr, "__setattr__": obj_setattr, "__del__": obj_del}
	LazyObject = type("LazyObject", (baseType,), attribs)
	return LazyObject()

def PersistentObject(baseType, filename):
	def load():
		import appinfo
		try:
			f = open(appinfo.userdir + "/" + filename)
		except IOError: # e.g. file-not-found. that's ok
			return baseType()

		obj = eval(f.read())
		assert isinstance(obj, baseType)
		return obj
	def save(obj):
		import appinfo
		f = open(appinfo.userdir + "/" + filename)
		f.write(betterRepr(obj))
		f.write("\n")
	def obj_repr(obj):
		return "PersistentObject(%r, %r)" % (baseType, filename)
	return ObjectProxy(load, delHook=save, baseType=baseType,
		custom_attribs={"save": save, "__repr__": obj_repr})
