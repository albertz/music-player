
from utils import *
import appinfo
import os
from threading import currentThread, Thread


class Module:
	def __init__(self, name, filename):
		self.name = name
		self.filename = filename
		self.thread = None
		self.module = None

	@property
	def mainFuncName(self): return self.name + "Main"

	@property
	def moduleName(self): return "mod_" + self.name

	def start(self):
		self.thread = Thread(target=self.threadMain, name=self.name + " main")
		self.thread.daemon = True # Our own exit-handler (see main()) will wait for them.
		self.thread.waitQueue = None
		self.thread.cancel = False
		self.thread.reload = False
		self.thread.start()

	def threadMain(self):
		better_exchook.install()
		thread = currentThread()
		setCurThreadName("PyMod %s" % self.name)
		while True:
			if self.module:
				try:
					reload_module(self.module)
				except Exception:
					print("couldn't reload module", self.module)
					sys.excepthook(*sys.exc_info())
					# continue anyway, maybe it still works and maybe the mainFunc does sth good/important
			else:
				self.module = __import__(self.moduleName)
			mainFunc = getattr(self.module, self.mainFuncName)
			try:
				mainFunc()
			except KeyboardInterrupt:
				break
			except Exception:
				print("Exception in module", self.name)
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

	def __repr__(self):
		return "<Module %s %r>" % (self.name, self.thread)



try:
	modules
except NameError:
	modules = []

def getModule(modname):
	for m in modules:
		if m.name == modname: return m
	return None

Paths = [appinfo.userdir + "/modules", appinfo.mydir + "/modules"]

def scanModules():
	from glob import glob
	for path in Paths:
		if path not in sys.path:
			sys.path.append(path)
		for fn in glob(path + "/mod_*.py"):
			modname = os.path.basename(fn)[4:-3]
			if not getModule(modname):
				modules.append(Module(modname, fn))

scanModules()


def reloadModules():
	# reload some custom random Python modules
	import utils
	reload_module(utils)
	import Song, State
	reload_module(Song)
	reload_module(State)
	# reload all our modules
	for m in modules:
		m.reload()


