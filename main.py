#!/usr/bin/python

import better_exchook
better_exchook.install()

from utils import *
from pprint import pprint
from threading import Thread

from State import state, playerMain

class Module:
	def __init__(self, name):
		self.name = name
		self.thread = Thread(target = self.threadMain, name = name + " main")
		self.module = None
	@property
	def mainFuncName(self): return self.name + "Main"
	@property
	def moduleName(self): return self.name
	def start(self): self.thread.start()
	def threadMain(self):
		better_exchook.install()
		if self.mainFuncName in globals():
			mainFunc = globals()[self.mainFuncName]
		else:
			if self.module:
				reload(self.module)
			else:
				self.module = __import__(self.moduleName)
			mainFunc = getattr(self.module, self.mainFuncName)
		mainFunc()
	def stop(self): self.thread.join()

modules = map(Module, [
	"player",
	"tracker",
	"mediakeys",
	"gui",
])

if __name__ == '__main__':	
	import time, os, sys
	loopFunc = lambda: time.sleep(10)
	if os.isatty(sys.stdin.fileno()):
		# If we are a TTY, do some very simple input handling.
		setTtyNoncanonical(sys.stdin.fileno())
		def handleInput():
			global player
			ch = os.read(sys.stdin.fileno(),7)
			if ch == "q": sys.exit(0)
			try:
				if ch == "\x1b[D": # left
					state.player.seekRel(-10)
				elif ch == "\x1b[C": #right
					state.player.seekRel(10)
				elif ch == "\n": # return
					state.player.nextSong()
				elif ch == " ":
					state.player.playing = not state.player.playing
			except:
				sys.excepthook(*sys.exc_info())
		loopFunc = handleInput

	for m in modules: m.start()
	while True:
		try: loopFunc() # wait for KeyboardInterrupt
		except BaseException, e:
			state.updates.put((e, (), {}))
			state.updates.cancelAll()
			break
	for m in modules: m.stop()
	
	