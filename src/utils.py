# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import sys
from collections import deque
import time
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

class Uninitialized: pass

class initBy(object):
	def __init__(self, initFunc, name=None):
		self.initFunc = initFunc
		self.name = name or initFunc.func_name
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
	import types
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

def ObjectProxy(lazyLoader, customAttribs={}, baseType=object, typeName="ObjectProxy"):
	class Value: pass
	obj = Value()
	attribs = customAttribs.copy()
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
	LazyObject = type(typeName, (object,), attribs)
	lazyObjInst = LazyObject()
	return lazyObjInst

def PersistentObject(
		baseType, filename, defaultArgs=(),
		persistentRepr = False, namespace = None,
		installAutosaveWrappersOn = (),
		autosaveOnDel = True,
		customAttribs = {}):
	betterRepr = globals()["betterRepr"] # save local copy
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
		try:
			obj = eval(f.read(), g)
		except Exception:
			import sys
			sys.excepthook(*sys.exc_info())
			return baseType(*defaultArgs)
			
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
	_customAttribs = {
		"save": save,
		"_isPersistentObject": True,
		"_filename": filename,
		"_persistentRepr": persistentRepr,
		"__repr__": obj_repr,
		}
	if autosaveOnDel:
		def obj_del(obj): save(obj)
		_customAttribs["__del__"] = obj_del
	def makeWrapper(funcAttrib):
		def wrapped(self, *args, **kwargs):
			obj = self.__get__(None)
			f = getattr(obj, funcAttrib)
			ret = f(*args, **kwargs)
			save(self)
			return ret
		return wrapped
	for attr in installAutosaveWrappersOn:
		_customAttribs[attr] = makeWrapper(attr)
	_customAttribs.update(customAttribs)
	return ObjectProxy(
		load,
		baseType = baseType,
		customAttribs = _customAttribs,
		typeName = "PersistentObject(%s)" % filename
	)


def test_ObjectProxy():
	expectedLoad = False
	class Test:
		def __init__(self): assert expectedLoad
		obj1 = object()
		obj2 = object()
	proxy = ObjectProxy(Test)
	expectedLoad = True
	assert proxy.obj1 is Test.obj1

	class Test(object):
		def __init__(self): assert expectedLoad
		obj1 = object()
		obj2 = object()
	proxy = ObjectProxy(Test, customAttribs = {"obj1": 42})
	expectedLoad = True
	assert proxy.obj1 is 42
	assert proxy.obj2 is Test.obj2
	
	from collections import deque
	proxy = ObjectProxy(deque, customAttribs = {"append": 42})
	assert proxy.append is 42
	
	
class DictObj(dict):
	def __getattr__(self, item): return self[item]
	def __setattr__(self, key, value): self[key] = value



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
	import objc
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


def ObjCClassAutorenamer(name, bases, dict):
	import objc
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
	"""
	:rtype : unicode
	"""
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

def getTempNameInScope(scope):
	import random
	while True:
		name = "_tmp_" + "".join([str(random.randrange(0, 10)) for _ in range(10)])
		if name not in scope: return name


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

def ExceptionCatcherDecorator(func):
	def decoratedFunc(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except Exception:
			sys.excepthook(*sys.exc_info())			
	return decoratedFunc



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


def debugFindThread(threadName):
	import threading
	for th in threading.enumerate():
		if th.name == threadName: return th
	return None

def debugGetThreadStack(threadName):
	th = debugFindThread(threadName)
	assert th, "thread not found"
	stack = sys._current_frames()[th.ident]
	return th, stack

def debugGetLocalVarFromThread(threadName, funcName, varName):
	th, stack = debugGetThreadStack(threadName)
	_tb = stack
	limit = None
	n = 0
	from inspect import isframe
	while _tb is not None and (limit is None or n < limit):
		if isframe(_tb): f = _tb
		else: f = _tb.tb_frame
		if f.f_code.co_name == funcName:
			if varName in f.f_locals:
				return f, f.f_locals[varName]
		if isframe(_tb): _tb = _tb.f_back
		else: _tb = _tb.tb_next
		n += 1		
	return None, None




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


def uniqList(l):
	s = set()
	l_new = []
	for v in l:
		if v in s: continue
		s.add(v)
		l_new.append(v)
	return l_new


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

