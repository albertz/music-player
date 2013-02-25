# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# Import PyObjC here. This is because the first import of PyObjC *must* be
# in the main thread. Otherwise, the NSAutoreleasePool created automatically
# by PyObjC on the first import would be released at exit by the main thread
# which would crash (because it was created in a different thread).
# http://pyobjc.sourceforge.net/documentation/pyobjc-core/intro.html
try:
	import objc
except ImportError:
	# probably not MacOSX. doesn't matter
	pass

from collections import deque
from threading import Condition, Thread, currentThread, Lock, RLock
import sys, os, time
import types

import better_exchook

# some global variable which indicates that we are quitting just right now
quit = False

class Id:
	"When you need some unique object with maybe some name, use this"
	name = None
	def __init__(self, name=None):
		self.name = name
	def __repr__(self):
		if self.name: return "<Id %s>" % self.name
		return "<Id %i>" % id(self)

class OnRequestQueue:
	class QueueEnd:
		def __init__(self, listType=deque):
			self.q = listType()
			self.cond = Condition()
			self.cancel = False
		def put(self, item):
			with self.cond:
				if self.cancel: return False
				self.q.append(item)
				self.cond.notify()
		def setCancel(self):
			with self.cond:
				self.cancel = True
				self.cond.notify()
	def __init__(self):
		self.queues = set()
	def put(self, item):
		for q in list(self.queues):
			q.put(item)
	def cancelAll(self):
		for q in list(self.queues):
			q.setCancel()
	def read(self, *otherQueues, **kwargs):
		q = self.QueueEnd(**kwargs)
		thread = currentThread()
		thread.waitQueue = q
		if thread.cancel:
			# This is to avoid a small race condition for the case
			# that the thread which wants to join+cancel us was faster
			# and didn't got the waitQueue. In that case, it would
			# have set the cancel already to True.
			return
		for reqqu in otherQueues: assert(isinstance(reqqu, OnRequestQueue))
		reqQueues = (self,) + otherQueues
		for reqqu in reqQueues: reqqu.queues.add(q)
		while True:
			with q.cond:
				l = []
				if len(q.q) > 0:
					l += [q.q.popleft()]
				cancel = q.cancel
				if not l and not cancel:
					q.cond.wait()
			for item in l:
				yield item
			if cancel: break
		for reqqu in reqQueues: reqqu.queues.remove(q)

class EventCallback:
	def __init__(self, targetQueue, name=None, extraCall=None):
		self.targetQueue = targetQueue
		self.name = name
		self.extraCall = extraCall
	def __call__(self, *args, **kwargs):
		if not "timestamp" in kwargs:
			kwargs["timestamp"] = time.time()
		if self.extraCall:
			self.extraCall(*args, **kwargs)
		self.targetQueue.put((self, args, kwargs))
	def __repr__(self):
		return "<EventCallback %s>" % self.name

class Event:
	def __init__(self):
		self.lock = RLock()
		self.targets = []
	def push(self, *args):
		with self.lock:
			targets = self.targets
			for weakt in targets:
				t = weakt() # resolve weakref
				if t: t(*args)
				else: self.targets.remove(weakt)
	def register(self, target):
		assert sys.getrefcount(target) > 1, "target will be weakrefed, thus we need more references to it"
		import weakref
		with self.lock:
			self.targets.append(weakref.ref(target))
		
class initBy(object):
	def __init__(self, initFunc):
		self.initFunc = initFunc
		self.name = initFunc.func_name
		self.attrName = "_" + self.name
	def load(self, inst):
		if not hasattr(inst, self.attrName):
			setattr(inst, self.attrName, self.initFunc(inst))
	def __get__(self, inst, type=None):
		if inst is None: # access through class
			return self
		self.load(inst)
		if hasattr(getattr(inst, self.attrName), "__get__"):
			return getattr(inst, self.attrName).__get__(inst, type)
		return getattr(inst, self.attrName)
	def __set__(self, inst, value):
		self.load(inst)
		if hasattr(getattr(inst, self.attrName), "__set__"):
			return getattr(inst, self.attrName).__set__(inst, value)
		setattr(inst, self.attrName, value)
		
class oneOf(object):
	def __init__(self, *consts):
		assert len(consts) > 0
		self.consts = consts
		self.value = consts[0]
	def __get__(self, inst, type=None):
		if inst is None: # access through class
			return self
		return self
	def __set__(self, inst, value):
		assert value in self.consts
		self.value = value

class UserAttrib(object):
	""" The idea/plan for this attrib type is:
	Use it in the GUI and display it nicely. Store every GUI related info here.
	I.e. this should say whether it is read-only to the user (if not visible to user at all ->
	 don't use this class), if it should be represented as a list, string, etc.
	 (this is the type, right now all Traits.TraitTypes), some other GUI decoration stuff,
	 etc.
	Note that this lays in the utils module because it is completely decoupled
	from the GUI. It only stores information which might be useful for a GUI.
	"""
	staticCounter = 0
	def __init__(self, name=None, type=None, writeable=False, updateHandler=None,
				 alignRight=False,
				 spaceX=None, spaceY=None,
				 width=None, height=None,
				 variableWidth=None, variableHeight=False,
				 autosizeWidth=False,
				 highlight=False, lowlight=False,
				 canHaveFocus=False,
				 withBorder=False,
				 searchLook=False,
				 autoScrolldown=False,
				 dragHandler=None,
				 selectionChangeHandler=None,
				 ):
		self.name = name
		self.type = type
		self.writeable = writeable
		self.updateHandler = updateHandler
		self.alignRight = alignRight
		self.spaceX = spaceX
		self.spaceY = spaceY
		self.width = width
		self.height = height
		self.variableWidth = variableWidth
		self.variableHeight = variableHeight
		self.autosizeWidth = autosizeWidth
		self.highlight = highlight
		self.lowlight = lowlight
		self.canHaveFocus = canHaveFocus
		self.withBorder = withBorder
		self.searchLook = searchLook
		self.autoScrolldown = autoScrolldown
		self.dragHandler = dragHandler
		self.selectionChangeHandler = selectionChangeHandler
		self.__class__.staticCounter += 1
		# Keep an index. This is so that we know the order of initialization later on.
		# This is better for the GUI representation so we can order it the same way
		# as it is defined in the class.
		# iterUserAttribs() uses this.
		self.index = self.__class__.staticCounter
	def getTypeClass(self):
		import inspect
		if inspect.isclass(self.type): return self.type
		return self.type.__class__
	def isType(self, T):
		return issubclass(self.getTypeClass(), T)
	@staticmethod
	def _getUserAttribDict(inst):
		if not hasattr(inst, "__userAttribs"):
			setattr(inst, "__userAttribs", {})
		return inst.__userAttribs
	@classmethod
	def _get(cls, name, inst):
		return cls._getUserAttribDict(inst)[name]
	def get(self, inst):
		try: return self._get(self.name, inst)
		except KeyError: return self.value
	def __get__(self, inst, type=None):
		if inst is None: # access through class
			return self
		if hasattr(self.value, "__get__"):
			return self.value.__get__(inst, type)
		return self.get(inst)
	@property
	def callDeco(self):
		class Wrapper:
			def __getattr__(_self, item):
				f = getattr(self.value, item)
				def wrappedFunc(arg): # a decorator expects a single arg
					value = f(arg)
					return self(value)
				return wrappedFunc
		return Wrapper()
	def setUpdateEvent(self, updateProp):
		self._updates = updateProp
		return updateProp
	def hasUpdateEvent(self):
		return getattr(self, "_updates", None)
	def updateEvent(self, inst, type=None):
		return self._updates.__get__(inst, type)
	@classmethod
	def _set(cls, name, inst, value):
		cls._getUserAttribDict(inst)[name] = value
	def set(self, inst, value):
		self._set(self.name, inst, value)
	def __set__(self, inst, value):
		if inst is None: # access through class
			self.value = value
			return
		if hasattr(self.value, "__set__"):
			return self.value.__set__(inst, value)
		self.set(inst, value)
	@classmethod
	def _getName(cls, obj):
		if hasattr(obj, "name"): return obj.name
		elif hasattr(obj, "func_name"): return obj.func_name
		elif hasattr(obj, "fget"): return cls._getName(obj.fget)
		return None
	def __call__(self, attrib):
		if not self.name:
			self.name = self._getName(attrib)
		self.value = attrib
		return self
	def __repr__(self):
		return "<UserAttrib %s, %r>" % (self.name, self.type)

def iterUserAttribs(obj):
	attribs = []
	for attribName in dir(obj.__class__):
		attrib = getattr(obj.__class__, attribName)
		if attrib.__class__.__name__ == "UserAttrib":
			attribs += [attrib]
	attribs.sort(key = lambda attr: attr.index)
	return attribs

class safe_property(object):
	def __init__(self, prop):
		self.prop = prop
	def __get__(self, instance, owner):
		if instance is None: return self
		try:
			return self.prop.__get__(instance, owner)
		except AttributeError:
			# We should never reraise this particular exception. Thus catch it here.
			sys.excepthook(*sys.exc_info())
			return None # The best we can do.
	def __set__(self, inst, value):
		try:
			self.prop.__set__(inst, value)
		except AttributeError:
			# We should never reraise this particular exception. Thus catch it here.
			sys.excepthook(*sys.exc_info())
	def __getattr__(self, attr):
		# forward prop.setter, prop.deleter, etc.
		return getattr(self.prop, attr)

def formatDate(t):
	if isinstance(t, (types.IntType,types.LongType,types.FloatType)):
		t = time.gmtime(t)
	return time.strftime("%Y-%m-%d %H:%M:%S +0000", t)

def formatTime(t):
	if t is None: return "?"
	t = round(t)
	mins = long(t // 60)
	t -= mins * 60
	hours = mins // 60
	mins -= hours * 60
	if hours: return "%02i:%02i:%02.0f" % (hours,mins,t)
	return "%02i:%02.0f" % (mins,t)

def formatFilesize(s):
	L = 800
	Symbols = ["byte", "KB", "MB", "GB", "TB"]
	i = 0
	while True:
		if s < L: break
		if i == len(Symbols) - 1: break
		s /= 1024.
		i += 1
	return "%.3g %s" % (s, Symbols[i])

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

def takeN(iterator, n):
	i = 0
	l = [None] * n
	while i < n:
		try:
			l[i] = next(iterator)
		except StopIteration:
			l = l[0:i]
			break
		i += 1
	return l

def attrChain(base, *attribs, **kwargs):
	default = kwargs.get("default", None)
	obj = base
	for attr in attribs:
		if obj is None: return default
		obj = getattr(obj, attr, None)
	if obj is None: return default
	return obj

def ObjectProxy(lazyLoader, custom_attribs={}, baseType=object):
	class Value: pass
	obj = Value()
	attribs = custom_attribs.copy()
	def load():
		if not hasattr(obj, "value"):
			obj.value = lazyLoader()
	def obj_getattribute(self, key):
		try:
			return object.__getattribute__(self, key)				
		except AttributeError:
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
	attribs.update({
		"__getattribute__": obj_getattribute,
		"__setattr__": obj_setattr,
		"__get__": obj_desc_get,
		"__set__": obj_desc_set,
		})
	# just set them so that we have them in the class. needed for __len__, __str__, etc.
	for a in dir(baseType):
		if a == "__new__": continue
		if a == "__init__": continue
		if a in attribs.keys(): continue
		class WrapProp(object):
			def __get__(self, inst, type=None, attrib=a):
				if inst is lazyObjInst:
					load()
					return object.__getattribute__(obj.value, attrib)
				return getattr(baseType, attrib)					
		attribs[a] = WrapProp()
	LazyObject = type("LazyObject", (object,), attribs)
	lazyObjInst = LazyObject()
	return lazyObjInst

def PersistentObject(baseType, filename, defaultArgs=(), persistentRepr = False, namespace = None):
	import appinfo
	fullfn = appinfo.userdir + "/" + filename
	def load():
		try:
			f = open(fullfn)
		except IOError: # e.g. file-not-found. that's ok
			return baseType(*defaultArgs)

		# some common types
		g = {baseType.__name__: baseType} # the baseType itself
		if namespace is None:
			g.update(globals()) # all what we have here
			if baseType.__module__:
				# the module of the basetype
				import sys
				m = sys.modules[baseType.__module__]
				g.update([(varname,getattr(m,varname)) for varname in dir(m)])
		else:
			g.update(namespace)
		obj = eval(f.read(), g)
		# Try to convert.
		if not isinstance(obj, baseType):
			obj = baseType(obj)
		return obj
	def save(obj):
		s = betterRepr(obj.__get__(None))
		f = open(fullfn, "w")
		f.write(s)
		f.write("\n")
		f.close()
	def obj_repr(obj):
		if persistentRepr:
			return "PersistentObject(%s, %r, persistentRepr=True)" % (baseType.__name__, filename)
		return betterRepr(obj.__get__(None))
	def obj_del(obj):
		save(obj)
	return ObjectProxy(load, baseType=baseType,
		custom_attribs={
			"save": save,
			"_isPersistentObject": True,
			"_filename": filename,
			"_persistentRepr": persistentRepr,
			"__repr__": obj_repr,
			"__del__": obj_del,
			})


class DictObj(dict):
	def __getattr__(self, item): return self[item]
	def __setattr__(self, key, value): self[key] = value


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
			if self.module:
				try:
					reload(self.module)
				except Exception:
					print "couldn't reload module", self.module
					sys.excepthook(*sys.exc_info())
					# continue anyway, maybe it still works and maybe the mainFunc does sth good/important
			else:
				self.module = __import__(self.moduleName)
			mainFunc = getattr(self.module, self.mainFuncName)
			try:
				mainFunc()
			except Exception:
				print "Exception in thread", thread.name
				sys.excepthook(*sys.exc_info())
			if not thread.reload: break
			sys.stdout.write("reloading module %s\n" % self.name)
			thread.cancel = False
			thread.reload = False
			thread.waitQueue = None
	def stop(self, join=True):
		if not self.thread: return
		waitQueue = self.thread.waitQueue # save a ref in case the other thread already removes it
		self.thread.cancel = True
		if waitQueue: waitQueue.setCancel()
		if join:
			timeout = 1
			while True:
				self.thread.join(timeout=timeout)
				if not self.thread.isAlive(): break
				sys.stdout.write("\n\nWARNING: module %s thread is hanging at stop\n" % self.name)
				dumpThread(self.thread.ident)
				timeout *= 2
				if timeout > 60: timeout = 60
	def reload(self):
		if self.thread and self.thread.isAlive():
			self.thread.reload = True
			self.stop(join=False)
		else:
			self.start()
	def __str__(self):
		return "Module %s" % self.name



def objc_disposeClassPair(className):
	# Be careful using this!
	# Any objects holding refs to the old class will be invalid
	# and will probably crash!
	# Creating a new class after it will not make them valid because
	# the new class will be at a different address.

	# some discussion / example:
	# http://stackoverflow.com/questions/7361847/pyobjc-how-to-delete-existing-objective-c-class
	# https://github.com/albertz/chromehacking/blob/master/disposeClass.py

	import ctypes

	ctypes.pythonapi.objc_lookUpClass.restype = ctypes.c_void_p
	ctypes.pythonapi.objc_lookUpClass.argtypes = (ctypes.c_char_p,)

	addr = ctypes.pythonapi.objc_lookUpClass(className)
	if not addr: return False

	ctypes.pythonapi.objc_disposeClassPair.restype = None
	ctypes.pythonapi.objc_disposeClassPair.argtypes = (ctypes.c_void_p,)

	ctypes.pythonapi.objc_disposeClassPair(addr)


def objc_setClass(obj, clazz):
	objAddr = objc.pyobjc_id(obj) # returns the addr and also ensures that it is an objc object
	assert objAddr != 0

	import ctypes

	ctypes.pythonapi.objc_lookUpClass.restype = ctypes.c_void_p
	ctypes.pythonapi.objc_lookUpClass.argtypes = (ctypes.c_char_p,)

	className = clazz.__name__ # this should be correct I guess
	classAddr = ctypes.pythonapi.objc_lookUpClass(className)
	assert classAddr != 0

	# Class object_setClass(id object, Class cls)
	ctypes.pythonapi.object_setClass.restype = ctypes.c_void_p
	ctypes.pythonapi.object_setClass.argtypes = (ctypes.c_void_p,ctypes.c_void_p)

	ctypes.pythonapi.object_setClass(objAddr, classAddr)

	obj.__class__ = clazz

def do_in_mainthread(f, wait=True):
	# Note: We don't need/want the NSThread.isMainThread() check and extra handling.
	# The `performSelectorOnMainThread:withObject:waitUntilDone:` does the right thing
	# in case we are the main thread: if wait is True, it is executed from here,
	# otherwise it is queued and executed in the next frame.
	
	global quit
	if quit:
		raise KeyboardInterrupt
	
	try:
		NSObject = objc.lookUpClass("NSObject")
		class PyAsyncCallHelper(NSObject):
			def initWithArgs_(self, f):
				self.f = f
				self.ret = None
				self.exc = None
				return self
			def call_(self, o):
				try:
					self.ret = self.f()
				except (KeyboardInterrupt,SystemExit) as exc:
					self.exc = exc
				except:
					print "Exception in PyAsyncCallHelper call"
					sys.excepthook(*sys.exc_info())					
	except Exception:
		PyAsyncCallHelper = objc.lookUpClass("PyAsyncCallHelper") # already defined earlier

	helper = PyAsyncCallHelper.alloc().initWithArgs_(f)
	helper.performSelectorOnMainThread_withObject_waitUntilDone_(helper.call_, None, wait)
	if wait and helper.exc:
		raise helper.exc
	return helper.ret

def DoInMainthreadDecorator(func):
	def decoratedFunc(*args, **kwargs):
		return do_in_mainthread(lambda: func(*args, **kwargs), wait=True)
	return decoratedFunc


def ObjCClassAutorenamer(name, bases, dict):
	def lookUpClass(name):
		try: return objc.lookUpClass(name)
		except objc.nosuchclass_error: return None
	if lookUpClass(name):
		numPostfix = 1
		while lookUpClass("%s_%i" % (name, numPostfix)):
			numPostfix += 1
		name = "%s_%i" % (name, numPostfix)
	return type(name, bases, dict)



def getMusicPathsFromDirectory(dir):
	import os, appinfo
	matches = []
	for root, dirnames, filenames in os.walk(dir):
		for filename in filenames:
			if filename.endswith(tuple(appinfo.formats)):
				matches.append(os.path.join(root, filename))

	return matches


def getSongsFromDirectory(dir):
	songs = []
	files = getMusicPathsFromDirectory(dir)
	from Song import Song
	for file in files:
		songs.append(Song(file))

	return songs


# A fuzzy set is a dict of values to [0,1] numbers.

def unionFuzzySets(*fuzzySets):
	resultSet = {}
	for key in set.union(*map(set, fuzzySets)):
		value = max(map(lambda x: x.get(key, 0), fuzzySets))
		if value > 0:
			resultSet[key] = value
	return resultSet

def intersectFuzzySets(*fuzzySets):
	resultSet = {}
	for key in set.intersection(*map(set, fuzzySets)):
		value = min(map(lambda x: x[key], fuzzySets))
		if value > 0:
			resultSet[key] = value
	return resultSet


def convertToUnicode(value):
	if isinstance(value, unicode): return value
	assert isinstance(value, str)
	try:
		value = value.decode("utf-8")
	except UnicodeError:
		try:
			value = value.decode() # default
		except UnicodeError:
			try:
				value = value.decode("iso-8859-1")
			except UnicodeError:
				value = value.decode("utf-8", "replace")
				#value = value.replace(u"\ufffd", "?")
	assert isinstance(value, unicode)
	return value

def fixValue(value, type):
	if not type: return value
	if isinstance(value, type): return value
	if type is unicode:
		if isinstance(value, str):
			return convertToUnicode(value)
		return unicode(value)
	return value


def iterGlobalsUsedInFunc(f, fast=False, loadsOnly=True):
	if hasattr(f, "func_code"): code = f.func_code
	elif hasattr(f, "im_func"): code = f.im_func.func_code
	else: code = f
	if fast:
		# co_names is the list of all names which are used.
		# These are mostly the globals.	These are also attrib names, so these are more...
		for name in code.co_names:
			yield name
	else:
		# Use the disassembly. Note that this will still not
		# find dynamic lookups to `globals()`
		# (which is anyway not possible to detect always).
		import dis
		ops = ["LOAD_GLOBAL"]
		if not loadsOnly:
			ops += ["STORE_GLOBAL", "DELETE_GLOBAL"]
		ops = map(dis.opmap.__getitem__, ops)
		i = 0
		while i < len(code.co_code):
			op = ord(code.co_code[i])
			i += 1
			if op >= dis.HAVE_ARGUMENT:
				oparg = ord(code.co_code[i]) + ord(code.co_code[i+1])*256
				i += 2
			else:
				oparg = None
			if op in ops:
				name = code.co_names[oparg]
				yield name

	# iterate through sub code objects
	import types
	for subcode in code.co_consts:
		if isinstance(subcode, types.CodeType):
			for g in iterGlobalsUsedInFunc(subcode, fast=fast, loadsOnly=loadsOnly):
				yield g


def iterGlobalsUsedInClass(clazz, module=None):
	import types
	for attrName in dir(clazz):
		attr = getattr(clazz, attrName)
		while True: # resolve props
			if isinstance(attr, safe_property):
				attr = attr.prop
				continue
			if isinstance(attr, property):
				attr = attr.fget
				continue
			break
		if isinstance(attr, (types.FunctionType, types.MethodType)):
			if module:
				if attr.__module__ != module:
					continue
			for g in iterGlobalsUsedInFunc(attr): yield g
			
# This is needed in some cases to avoid pickling problems with bounded funcs.
def funcCall(attrChainArgs, args=()):
	f = attrChain(*attrChainArgs)
	return f(*args)


import pickle, types, marshal
Unpickler = pickle.Unpickler
CellType = type((lambda x: lambda: x)(0).func_closure[0])
def makeCell(value): return (lambda: value).func_closure[0]
def getModuleDict(modname): return __import__(modname).__dict__
class Pickler(pickle.Pickler):
	def __init__(self, *args, **kwargs):
		if not "protocol" in kwargs:
			kwargs["protocol"] = pickle.HIGHEST_PROTOCOL
		pickle.Pickler.__init__(self, *args, **kwargs)
	dispatch = pickle.Pickler.dispatch.copy()

	def save_func(self, obj):
		try:
			self.save_global(obj)
			return
		except pickle.PicklingError:
			pass
		assert type(obj) is types.FunctionType
		self.save(types.FunctionType)
		self.save((
			obj.func_code,
			obj.func_globals,
			obj.func_name,
			obj.func_defaults,
			obj.func_closure,
			))
		self.write(pickle.REDUCE)
		self.memoize(obj)
	dispatch[types.FunctionType] = save_func

	def save_code(self, obj):
		assert type(obj) is types.CodeType
		self.save(marshal.loads)
		self.save((marshal.dumps(obj),))
		self.write(pickle.REDUCE)
		self.memoize(obj)
	dispatch[types.CodeType] = save_code

	def save_cell(self, obj):
		assert type(obj) is CellType
		self.save(makeCell)
		self.save((obj.cell_contents,))
		self.write(pickle.REDUCE)
		self.memoize(obj)
	dispatch[CellType] = save_cell
	
	# We also search for module dicts and reference them.
	def intellisave_dict(self, obj):
		if len(obj) <= 5: # fastpath
			self.save_dict(obj)
			return
		for modname, mod in sys.modules.iteritems():
			if not mod: continue
			moddict = mod.__dict__
			if obj is moddict:
				self.save(getModuleDict)
				self.save((modname,))
				self.write(pickle.REDUCE)
				self.memoize(obj)
				return
		self.save_dict(obj)
	dispatch[types.DictionaryType] = intellisave_dict

	# Some types in the types modules are not correctly referenced,
	# such as types.FunctionType. This is fixed here.
	def fixedsave_type(self, obj):
		try:
			self.save_global(obj)
			return
		except pickle.PicklingError:
			pass
		for modname in ["types"]:
			moddict = sys.modules[modname].__dict__
			for modobjname,modobj in moddict.iteritems():
				if modobj is obj:
					self.write(pickle.GLOBAL + modname + '\n' + modobjname + '\n')
					self.memoize(obj)
					return
		self.save_global(obj)
	dispatch[types.TypeType] = fixedsave_type

	# avoid pickling instances of ourself. this mostly doesn't make sense and leads to trouble.
	# however, also doesn't break. it mostly makes sense to just ignore.
	def __getstate__(self): return None
	def __setstate__(self, state): pass

class ExecingProcess:
	def __init__(self, target, args, name):
		self.target = target
		self.args = args
		self.name = name
		self.daemon = True
		self.pid = None
	def start(self):
		assert self.pid is None
		def pipeOpen():
			readend,writeend = os.pipe()
			readend = os.fdopen(readend, "r")
			writeend = os.fdopen(writeend, "w")
			return readend,writeend
		self.pipe_c2p = pipeOpen()
		self.pipe_p2c = pipeOpen()
		pid = os.fork()
		if pid == 0: # child
			self.pipe_c2p[0].close()
			self.pipe_p2c[1].close()
			args = sys.argv + [
				"--forkExecProc",
				str(self.pipe_c2p[1].fileno()),
				str(self.pipe_p2c[0].fileno())]
			os.execv(args[0], args)
		else: # parent
			self.pipe_c2p[1].close()
			self.pipe_p2c[0].close()
			self.pid = pid
			self.pickler = Pickler(self.pipe_p2c[1])
			self.pickler.dump(self.name)
			self.pickler.dump(self.target)
			self.pickler.dump(self.args)
			self.pipe_p2c[1].flush()
	@staticmethod
	def checkExec():
		if "--forkExecProc" in sys.argv:
			argidx = sys.argv.index("--forkExecProc")
			writeFileNo = int(sys.argv[argidx + 1])
			readFileNo = int(sys.argv[argidx + 2])
			readend = os.fdopen(readFileNo, "r")
			writeend = os.fdopen(writeFileNo, "w")
			unpickler = Unpickler(readend)
			name = unpickler.load()
			print "ExecingProcess child %s (pid %i)" % (name, os.getpid())
			try:
				target = unpickler.load()
				args = unpickler.load()
			except EOFError:
				print "Error: unpickle incomplete"
				raise SystemExit
			ret = target(*args)
			Pickler(writeend).dump(ret)
			print "ExecingProcess child %s (pid %i) finished" % (name, os.getpid())
			raise SystemExit

class ExecingProcess_ConnectionWrapper(object):
	def __init__(self, fd=None):
		self.fd = fd
		if self.fd:
			from _multiprocessing import Connection
			self.conn = Connection(fd)
	def __getstate__(self): return self.fd
	def __setstate__(self, state): self.__init__(state)
	def __getattr__(self, attr): return getattr(self.conn, attr)
		
def ExecingProcess_Pipe():
	import socket
	s1, s2 = socket.socketpair()
	c1 = ExecingProcess_ConnectionWrapper(os.dup(s1.fileno()))
	c2 = ExecingProcess_ConnectionWrapper(os.dup(s2.fileno()))
	s1.close()
	s2.close()
	return c1, c2

isFork = False

class AsyncTask:		
	def __init__(self, func, name=None, mustExec=False):
		self.name = name or "unnamed"
		self.func = func
		self.mustExec = mustExec
		self.parent_pid = os.getpid()
		if mustExec and sys.platform != "win32":
			self.Process = ExecingProcess
			self.Pipe = ExecingProcess_Pipe
		else:
			from multiprocessing import Process, Pipe
			self.Process = Process
			self.Pipe = Pipe
		self.parent_conn, self.child_conn = self.Pipe()
		self.proc = self.Process(
			target = funcCall,
			args = ((AsyncTask, "_asyncCall"), (self,)),
			name = self.name + " worker process")
		self.proc.daemon = True		
		self.proc.start()
		self.child_conn.close()
		self.child_pid = self.proc.pid
		assert self.child_pid
		self.conn = self.parent_conn
		
	@staticmethod
	def _asyncCall(self):
		assert self.isChild
		self.parent_conn.close()
		self.conn = self.child_conn # we are the child
		if not self.mustExec and sys.platform != "win32":
			global isFork
			isFork = True
		try:
			self.func(self)
		except KeyboardInterrupt:
			print "Exception in AsyncTask", self.name, ": KeyboardInterrupt"
		except:
			print "Exception in AsyncTask", self.name
			sys.excepthook(*sys.exc_info())
		finally:
			self.conn.close()
	
	def put(self, value):
		self.conn.send(value)
		
	def get(self):
		thread = currentThread()
		try:
			thread.waitQueue = self
			res = self.conn.recv()
		except EOFError: # this happens when the child died
			raise ForwardedKeyboardInterrupt()
		except Exception:
			raise
		finally:
			thread.waitQueue = None
		return res
	
	@property
	def isParent(self):
		return self.parent_pid == os.getpid()

	@property
	def isChild(self):
		if self.isParent: return False
		assert self.parent_pid == os.getppid()		
		return True
	
	# This might be called from the module code.
	# See OnRequestQueue which implements the same interface.
	def setCancel(self):
		self.conn.close()
		if self.isParent and self.child_pid:
			import signal
			os.kill(self.child_pid, signal.SIGINT)
			self.child_pid = None
			
	@classmethod
	def test(cls):
		pass

class ForwardedKeyboardInterrupt(Exception): pass

def asyncCall(func, name=None, mustExec=False):
	def doCall(queue):
		res = None
		try:
			res = func()
			queue.put((None,res))
		except KeyboardInterrupt as exc:
			print "Exception in asyncCall", name, ": KeyboardInterrupt"
			queue.put((ForwardedKeyboardInterrupt(exc),None))
		except BaseException as exc:
			print "Exception in asyncCall", name
			sys.excepthook(*sys.exc_info())
			queue.put((exc,None))
	task = AsyncTask(func=doCall, name=name, mustExec=mustExec)
	# If there is an unhandled exception in doCall or the process got killed/segfaulted or so,
	# this will raise an EOFError here.
	# However, normally, we should catch all exceptions and just reraise them here.
	exc,res = task.get()
	if exc is not None:
		raise exc
	return res


def WarnMustNotBeInForkDecorator(func):
	class Ctx:
		didWarn = False
	def decoratedFunc(*args, **kwargs):
		global isFork
		if isFork:
			if not Ctx.didWarn:
				debugWarn("Must not be in fork!")
				Ctx.didWarn = True
			return None
		return func(*args, **kwargs)
	return decoratedFunc


def ExceptionCatcherDecorator(func):
	def decoratedFunc(*args, **kwargs):
		try:
			ret = func(*args, **kwargs)
		except Exception:
			sys.excepthook(*sys.exc_info())			
		return ret
	return decoratedFunc


class QueuedDaemonThread:
	def __init__(self):
		self.lock = RLock()
		self.cond = Condition(self.lock)
		self.queues = {}
		self.thread = None
		self.quit = False
	def _getHandler(self, queueItem):
		def handle():
			try:
				queueItem["func"]()
			except (ForwardedKeyboardInterrupt, KeyboardInterrupt, SystemExit):
				return # just ignore
			except BaseException:
				print "Exception in QueuedDaemonThread", queueItem["name"]
				sys.excepthook(*sys.exc_info())
			finally:
				with self.lock:
					queueItem["finished"] = True
					self.cond.notifyAll()
		return handle
	def _threadMain(self):
		while True:
			with self.lock:
				if self.quit:
					self.thread = None
					return
				for queueId,queue in self.queues.items():
					while queue:
						queueItem = queue[0]
						if queueItem.get("finished", False):
							queue.pop(0)
							continue
						if not queueItem.get("started", False):
							queueItem["started"] = True
							handler = self._getHandler(queueItem)
							daemonThreadCall(handler, name=queueItem["name"])
						break
					if not queue:
						del self.queues[queueId]
				self.cond.wait()
	def _maybeStart(self):
		if not self.thread:
			self.thread = daemonThreadCall(self._threadMain, name="queued daemon thread")
	def push(self, func, name=None, queue=None):
		assert queue
		with self.lock:
			self.queues.setdefault(queue, []).append({"func":func, "name":name})
			self.cond.notifyAll()
			self._maybeStart()
	def quit(self):
		with self.lock:
			self.quit = True
			self.cond.notifyAll()
queuedDaemonThread = QueuedDaemonThread()

def daemonThreadCall(func, name=None, queue=None):
	if queue:
		queuedDaemonThread.push(func, name=name, queue=queue)
		return
	def doCall():
		try:
			func()
		except (ForwardedKeyboardInterrupt, KeyboardInterrupt):
			return # just ignore
		except BaseException:
			print "Exception in daemonThreadCall thread", name
			sys.excepthook(*sys.exc_info())
	thread = Thread(target = doCall, name = name)
	thread.daemon = True
	thread.start()
	return thread


class AsyncInterrupt(BaseException): pass

# Note that there are places where an exception should never occur -
# eg inside an Lock.aquire(), Lock.__enter__(), Lock.__exit__().
# Otherwise we might end up with a non-unlocked mutex.
# We can never know if this is the case for the thread or not -
# so this is unsafe and should not be used!
# At least for now, I don't really see a way to overcome this.
def raiseExceptionInThread(threadId, exc=AsyncInterrupt):
	import ctypes
	ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(
		ctypes.c_long(threadId),
		ctypes.py_object(exc))
	# returns the count of threads where we set the exception
	if ret > 1:
		# strange - should not happen.
		print "Error: PyThreadState_SetAsyncExc returned >1"
		# try to reset - although this is similar unsafe...
		ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(threadId), None)
	return ret > 0


def killMeHard():
	import sys, os, signal
	os.kill(0, signal.SIGKILL)
	
def dumpAllThreads():
	import sys
	if not hasattr(sys, "_current_frames"):
		print "Warning: dumpAllThreads: no sys._current_frames"
		return

	import threading
	id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
	for threadId, stack in sys._current_frames().items():
		print("\n# Thread: %s(%d)" % (id2name.get(threadId,""), threadId))
		better_exchook.print_traceback(stack)

def dumpThread(threadId):
	import sys
	if not hasattr(sys, "_current_frames"):
		print "Warning: dumpThread: no sys._current_frames"
		return
	
	if threadId not in sys._current_frames():
		print("Thread %d not found" % threadId)
		return
	
	stack = sys._current_frames()[threadId]
	better_exchook.print_traceback(stack)

def debugWarn(msg):
	print "Warning:", msg
	import sys
	if not hasattr(sys, "_getframe"):
		print "Warning: debugWarn: no sys._getframe"
		return
	f = sys._getframe()
	if not f:
		print "Warning: debugWarn: no frame"
	f = f.f_back
	if not f:
		print "Warning: debugWarn: no previous frame"	
	better_exchook.print_traceback(f)
	

def test():
	AsyncTask.test()
	


def NSAutoreleasePoolDecorator(func):
	def decoratedFunc(*args, **kwargs):
		import AppKit
		pool = AppKit.NSAutoreleasePool.alloc().init()
		ret = func(*args, **kwargs)
		del pool
		return ret
	return decoratedFunc

def simplifyString(s):
	s = convertToUnicode(s)
	s = s.lower()
	import unicodedata
	s = unicodedata.normalize('NFD', s)
	s = u"".join([c for c in s if unicodedata.category(c) != 'Mn'])
	for base,repl in (
		(u"я", "r"),
		(u"æ", "a"),
		(u"œ", "o"),
		(u"ø", "o"),
		(u"ɲ", "n"),
		(u"ß", "ss"),
		(u"©", "c"),
		(u"ð", "d"),
		(u"đ", "d"),
		(u"ɖ", "d"),
		(u"þ", "th"),
	):
		s = s.replace(base, repl)
	return s


def isPymoduleAvailable(mod):
	try:
		__import__(mod)
	except ImportError:
		return False
	return True


def interactive_py_compile(source, filename="<interactive>"):
	c = compile(source, filename, "single")

	# we expect this at the end:
	#   PRINT_EXPR     
	#   LOAD_CONST
	#   RETURN_VALUE   	
	import dis
	if ord(c.co_code[-5]) != dis.opmap["PRINT_EXPR"]:
		return c
	assert ord(c.co_code[-4]) == dis.opmap["LOAD_CONST"]
	assert ord(c.co_code[-1]) == dis.opmap["RETURN_VALUE"]
	
	code = c.co_code[:-5]
	code += chr(dis.opmap["RETURN_VALUE"])
	
	CodeArgs = [
		"argcount", "nlocals", "stacksize", "flags", "code",
		"consts", "names", "varnames", "filename", "name",
		"firstlineno", "lnotab", "freevars", "cellvars"]
	c_dict = dict([(arg, getattr(c, "co_" + arg)) for arg in CodeArgs])
	c_dict["code"] = code
	
	import types
	c = types.CodeType(*[c_dict[arg] for arg in CodeArgs])
	return c

