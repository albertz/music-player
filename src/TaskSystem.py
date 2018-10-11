
"""
Here are all subprocess, threading etc related utilities,
most of them quite low level.
"""

from __future__ import print_function
from utils import *
from threading import Condition, Thread, RLock, Lock, currentThread
import Logging
import sys
import os
try:
	from StringIO import StringIO
except ImportError:
	from io import StringIO
PY3 = sys.version_info[0] >= 3


def do_in_mainthread(f, wait=True):
	# Better use daemonThreadCall() instead.

	# Note: We don't need/want the NSThread.isMainThread() check and extra handling.
	# The `performSelectorOnMainThread:withObject:waitUntilDone:` does the right thing
	# in case we are the main thread: if wait is True, it is executed from here,
	# otherwise it is queued and executed in the next frame.

	global quit
	if quit:
		raise KeyboardInterrupt

	global isFork
	if isFork:
		Logging.debugWarn("called do_in_mainthread in fork")
		raise SystemError("called do_in_mainthread in fork")

	import objc
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
					print("Exception in PyAsyncCallHelper call")
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



def WarnMustNotBeInForkDecorator(func):
	class Ctx:
		didWarn = False
	def decoratedFunc(*args, **kwargs):
		global isFork
		if isFork:
			if not Ctx.didWarn:
				import Logging
				Logging.debugWarn("Must not be in fork!")
				Ctx.didWarn = True
			return None
		return func(*args, **kwargs)
	return decoratedFunc

def execInMainProc(func):
	global isMainProcess
	if isMainProcess:
		return func()
	else:
		assert _AsyncCallQueue.Self, "works only if called via asyncCall"
		return _AsyncCallQueue.Self.asyncExecClient(func)

def ExecInMainProcDecorator(func):
	def decoratedFunc(*args, **kwargs):
		return execInMainProc(lambda: func(*args, **kwargs))
	return decoratedFunc

def test_asyncCall():
	mod = globals()
	calledBackVarName = getTempNameInScope(mod)
	mod[calledBackVarName] = False
	def funcAsync():
		assert not isMainProcess
		assert not isFork
		res = execInMainProc(funcMain)
		assert res == "main"
		return "async"
	def funcMain():
		mod[calledBackVarName] = True
		return "main"
	res = asyncCall(funcAsync, name="test", mustExec=True)
	assert res == "async"
	assert mod[calledBackVarName] is True
	mod.pop(calledBackVarName)

class TestClassAsyncCallExecInMainProcDeco:
	def __init__(self, name):
		self.name = name
	@ExecInMainProcDecorator
	def testExecInMainProcDeco(self, *args):
		return 42, self.name, args
	@staticmethod
	def getInstance(name):
		return TestClassAsyncCallExecInMainProcDeco(name)
	def __reduce__(self):
		return (self.getInstance, (self.name,))

def test_asyncCall2():
	test = TestClassAsyncCallExecInMainProcDeco("test42")
	def funcAsync():
		res = test.testExecInMainProcDeco(1, buffer("abc"))
		assert res == (42, "test42", (1, buffer("abc")))
	asyncCall(funcAsync, name="test", mustExec=True)



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
		print("Error: PyThreadState_SetAsyncExc returned >1")
		# try to reset - although this is similar unsafe...
		ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(threadId), None)
	return ret > 0



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
				print("Exception in QueuedDaemonThread", queueItem["name"])
				sys.excepthook(*sys.exc_info())
			finally:
				with self.lock:
					queueItem["finished"] = True
					self.cond.notifyAll()
		return handle
	def _threadMain(self):
		setCurThreadName("Py QueuedDaemonThread")
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

def daemonThreadCall(func, args=(), name=None, queue=None):
	if queue:
		queuedDaemonThread.push(func, name=name, queue=queue)
		return
	def doCall():
		try:
			setCurThreadName("Py daemon: %s" % name)
			func(*args)
		except (ForwardedKeyboardInterrupt, KeyboardInterrupt):
			return # just ignore
		except BaseException:
			print("Exception in daemonThreadCall thread", name)
			sys.excepthook(*sys.exc_info())
	thread = Thread(target = doCall, name = name)
	thread.daemon = True
	thread.start()
	return thread



def test_AsyncTask():
	AsyncTask.test()



class ForwardedKeyboardInterrupt(Exception):
	pass

class _AsyncCallQueue:
	Self = None
	class Types:
		result = 0
		exception = 1
		asyncExec = 2
	def __init__(self, queue):
		assert not self.Self
		self.__class__.Self = self
		self.mutex = Lock()
		self.queue = queue
	def put(self, type, value):
		self.queue.put((type, value))
	def asyncExecClient(self, func):
		with self.mutex:
			self.put(self.Types.asyncExec, func)
			t, value = self.queue.get()
			if t == self.Types.result:
				return value
			elif t == self.Types.exception:
				raise value
			else:
				assert False, "bad behavior of asyncCall in asyncExec (%r)" % t
	@classmethod
	def asyncExecHost(clazz, task, func):
		q = task
		name = "<unknown>"
		try:
			name = repr(func)
			res = func()
		except Exception as exc:
			print("Exception in asyncExecHost", name, exc)
			q.put((clazz.Types.exception, exc))
		else:
			try:
				q.put((clazz.Types.result, res))
			except IOError:
				# broken pipe or so. parent quit. treat like a SIGINT
				raise KeyboardInterrupt

def asyncCall(func, name=None, mustExec=False):
	"""
	This executes func() in another process and waits/blocks until
	it is finished. The returned value is passed back to this process
	and returned. Exceptions are passed back as well and will be
	reraised here.

	If `mustExec` is set, the other process must `exec()` after the `fork()`.
	If it is not set, it might omit the `exec()`, depending on the platform.
	"""

	def doCall(queue):
		q = _AsyncCallQueue(queue)
		try:
			try:
				res = func()
			except KeyboardInterrupt as exc:
				print("Exception in asyncCall", name, ": KeyboardInterrupt")
				q.put(q.Types.exception, ForwardedKeyboardInterrupt(exc))
			except BaseException as exc:
				print("Exception in asyncCall", name)
				sys.excepthook(*sys.exc_info())
				q.put(q.Types.exception, exc)
			else:
				q.put(q.Types.result, res)
		except (KeyboardInterrupt, ForwardedKeyboardInterrupt):
			print("asyncCall: SIGINT in put, probably the parent died")
			# ignore

	task = AsyncTask(func=doCall, name=name, mustExec=mustExec)

	while True:
		# If there is an unhandled exception in doCall or the process got killed/segfaulted or so,
		# this will raise an EOFError here.
		# However, normally, we should catch all exceptions and just reraise them here.
		t,value = task.get()
		if t == _AsyncCallQueue.Types.result:
			return value
		elif t == _AsyncCallQueue.Types.exception:
			raise value
		elif t == _AsyncCallQueue.Types.asyncExec:
			_AsyncCallQueue.asyncExecHost(task, value)
		else:
			assert False, "unknown _AsyncCallQueue type %r" % t



# This is needed in some cases to avoid pickling problems with bounded funcs.
def funcCall(attrChainArgs, args=()):
	f = attrChain(*attrChainArgs)
	return f(*args)


import pickle, types, marshal
Unpickler = pickle.Unpickler
if PY3:
	CellType = type((lambda x: lambda: x)(0).__closure__[0])
	def makeCell(value): return (lambda: value).__closure__[0]
else:
	CellType = type((lambda x: lambda: x)(0).func_closure[0])
	def makeCell(value): return (lambda: value).func_closure[0]
def getModuleDict(modname): return __import__(modname).__dict__
DictType = dict if PY3 else types.DictionaryType

try:
	_BasePickler = pickle._Pickler  # use the pure Python implementation
except AttributeError:
	_BasePickler = pickle.Pickler

class Pickler(_BasePickler):
	def __init__(self, *args, **kwargs):
		if "protocol" not in kwargs:
			kwargs["protocol"] = pickle.HIGHEST_PROTOCOL
		super(Pickler, self).__init__(*args, **kwargs)
	dispatch = _BasePickler.dispatch.copy()

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
	dispatch[DictType] = intellisave_dict

	if not PY3:
		def save_buffer(self, obj):
			self.save(buffer)
			self.save((str(obj),))
			self.write(pickle.REDUCE)
		dispatch[types.BufferType] = save_buffer

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

	if not PY3:
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
			# Copying all parameters is problematic (e.g. --pyshell).
			# sys.argv[0] is never "python", so it might be problematic
			# if it is not executable. However, it should be.
			args = sys.argv[0:1] + [
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
	Verbose = False
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
			if ExecingProcess.Verbose: print("ExecingProcess child %s (pid %i)" % (name, os.getpid()))
			try:
				target = unpickler.load()
				args = unpickler.load()
			except EOFError:
				print("Error: unpickle incomplete")
				raise SystemExit
			ret = target(*args)
			Pickler(writeend).dump(ret)
			if ExecingProcess.Verbose: print("ExecingProcess child %s (pid %i) finished" % (name, os.getpid()))
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
	def _check_closed(self): assert not self.conn.closed
	def _check_writable(self): assert self.conn.writable
	def _check_readable(self): assert self.conn.readable
	def send(self, value):
		self._check_closed()
		self._check_writable()
		buf = StringIO()
		Pickler(buf).dump(value)
		self.conn.send_bytes(buf.getvalue())
	def recv(self):
		self._check_closed()
		self._check_readable()
		buf = self.conn.recv_bytes()
		f = StringIO(buf)
		return Unpickler(f).load()

def ExecingProcess_Pipe():
	import socket
	s1, s2 = socket.socketpair()
	c1 = ExecingProcess_ConnectionWrapper(os.dup(s1.fileno()))
	c2 = ExecingProcess_ConnectionWrapper(os.dup(s2.fileno()))
	s1.close()
	s2.close()
	return c1, c2


isFork = False  # fork() without exec()
isMainProcess = True

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
		global isMainProcess
		isMainProcess = False
		try:
			self.func(self)
		except KeyboardInterrupt:
			print("Exception in AsyncTask", self.name, ": KeyboardInterrupt")
		except BaseException:
			print("Exception in AsyncTask", self.name)
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



def test_picklebuffer():
	origbuffer = buffer("123")
	f = StringIO()
	Pickler(f).dump(origbuffer)
	f.seek(0)
	b = Unpickler(f).load()
	assert origbuffer == b





from contextlib import contextmanager

class ReadWriteLock(object):
	"""Classic implementation of ReadWriteLock.
	Note that this partly supports recursive lock usage:
	- Inside a readlock, a writelock will always block!
	- Inside a readlock, another readlock is fine.
	- Inside a writelock, any other writelock or readlock is fine.
	"""
	def __init__(self):
		import threading
		self.lock = threading.RLock()
		self.writeReadyCond = threading.Condition(self.lock)
		self.readerCount = 0
	@property
	@contextmanager
	def readlock(self):
		with self.lock:
			self.readerCount += 1
		try: yield
		finally:
			with self.lock:
				self.readerCount -= 1
				if self.readerCount == 0:
					self.writeReadyCond.notifyAll()
	@property
	@contextmanager
	def writelock(self):
		with self.lock:
			while self.readerCount > 0:
				self.writeReadyCond.wait()
			yield


