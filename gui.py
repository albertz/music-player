
import sys

if sys.platform != "darwin":
	print "GUI: your platform is probably not supported yet"
	def guiMain(): pass

import objc
from AppKit import *
from collections import deque

try: pools
except NameError: pools = deque()

# just in case that we are not the main thread
pools.append(NSAutoreleasePool.alloc().init())

import os, sys
from State import state, modules
from utils import *

mydir = os.path.dirname(__file__) or os.getcwd()
try:
	app
except NameError: # only declare if not yet declared
	app = None

def setupAppleMenu():

	# http://www.cocoabuilder.com/archive/cocoa/192181-initializing-the-menubar-without-interface-builder.html
	# By Robert Nikander

	mainMenu = NSMenu.alloc().initWithTitle_("MainMenu")
	mi = mainMenu.addItemWithTitle_action_keyEquivalent_("Apple", None, "")
	m = NSMenu.alloc().initWithTitle_("Apple")

	# strange hack
	app.setAppleMenu_(m)
	mainMenu.setSubmenu_forItem_(m, mi)
	mi = m.addItemWithTitle_action_keyEquivalent_('Quit', 'terminate:', 'q')

	app.setMainMenu_(mainMenu)

	return m

def setupWindow():
	w = NSWindow.alloc().init()
	#w.makeMainWindow()
	return w

if "PyAppDelegate" in globals():
	# already declared, clean up
	def cleanupOld():
		# NOTE: What we do here might be dangerous! :)
		# The class is already declared and PyObjC class redeclaring is broken.
		# Remove Python refs.
		global PyAppDelegate
		del PyAppDelegate
		appDelegate = app.delegate()
		app.setDelegate_(None)
		assert appDelegate.retainCount() == 2 # local var + manual retain() in setup()
		appDelegate.release()
		del appDelegate
		import gc
		gc.collect() # just to be sure that we deallocate every ref now! important!
		# We cannot really ensure that the current app delegate has retainCount == 1,
		# thus keep the obj and reset the class later!
		# This is dangerous without locking the object. For now, just hope for the best... :P
		#objc.object_lock(app.delegate()).lock()
		# Dispose the class so we can redeclare it below.
		objc_disposeClassPair("PyAppDelegate")
		# In reloadModuleHandling(), we will recreate an instance and resetup.
	do_in_mainthread(cleanupOld, wait=True)

def setupAfterAppFinishedLaunching(delegate):
	state.quit = quit
	setupAppleMenu()
	delegate.mainWindow = setupWindow()
	print "setupAfterAppFinishedLaunching ready"

class PyAppDelegate(NSObject):
	def applicationDidFinishLaunching_(self, notification):
		print "AppDelegate didFinishLaunching"
		for m in modules: m.start()
		setupAfterAppFinishedLaunching(self)

	def applicationShouldTerminate_(self, app):
		print "AppDelegate quit"
		for m in modules: m.stop()
		return NSTerminateNow

	def userNotificationCenter_shouldPresentNotification_(self, notifCenter, notif):
		return True

def quit():
	app.terminate_(None)

def setup():
	icon = NSImage.alloc()
	icon.initWithContentsOfFile_(mydir + "/icon.icns")
	app.setApplicationIconImage_(icon)

	appDelegate = PyAppDelegate.alloc().init()
	app.setDelegate_(appDelegate)
	appDelegate.retain()

	app.finishLaunching()
	app.updateWindows()
	app.activateIgnoringOtherApps_(True)

try:
	isReload
except NameError:
	isReload = False
else:
	isReload = True

def reloadModuleHandling():
	print "GUI module reload handler ..."
	appDelegate = PyAppDelegate.alloc().init()
	app.setDelegate_(appDelegate)
	appDelegate.retain()
	setupAfterAppFinishedLaunching(appDelegate)

def guiMain():
	# This is run from the module system in another thread.
	# We handle some background tasks here.
	# For now, this is a simple stdin handler because the standard stdin handler will not run if we have a GUI.
	import stdinconsole
	fd = sys.stdin.fileno()
	if os.isatty(fd):
		stdinconsole.setTtyNoncanonical(fd, timeout=1)
	else:
		return # stdin handler probably not needed, so just exit this thread

	from threading import currentThread
	thread = currentThread()
	while not thread.cancel:
		ch = os.read(fd,7)
		if ch:
			stdinconsole.handleInput(ch)

def main():
	""" This is called from main.py and will enter the NSApp main loop """
	assert NSThread.isMainThread()
	global app

	app = NSApplication.sharedApplication()
	setup()

	print "entering GUI main loop"
	app.run()

	sys.exit()

if isReload:
	do_in_mainthread(reloadModuleHandling)

if __name__ == "__main__":
	main()

# keep old pools. there is no real safe way to know whether we still have some refs to objects
