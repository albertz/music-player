
import sys

if sys.platform != "darwin":
	print "GUI: your platform is probably not supported yet"
	def guiMain(): pass

import objc
from AppKit import *
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
	w.makeMainWindow()
	return w

try:
	PyAppDelegate
except NameError: pass # normally declare below
else: # already declared
	# NOTE: What we do here might be dangerous! :)
	# The class is already declared and PyObjC class redeclaring is broken.
	# Thus, remove the earlier object instance:
	oldDelegate = app.delegate()
	app.setDelegate_(None)
	assert oldDelegate.retainCount() == 1 # otherwise the dispose will lead to a crash at some later point!
	del oldDelegate
	# Dispose the class so we can redeclare it below.
	objc_disposeClassPair("PyAppDelegate")
	# In reloadModuleHandling(), we will recreate an instance and resetup.

class PyAppDelegate(NSObject):
	def applicationDidFinishLaunching_(self, notification):
		print "AppDelegate didFinishLaunching"
		setupAppleMenu()
		state.quit = quit
		for m in modules: m.start()

		self.mainWindow = setupWindow()

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
	setup() # resetup. resets the app delegate, etc.
	app.delegate().applicationDidFinishLaunching_(None) # recall. might have important additional setup

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
	reloadModuleHandling()

if __name__ == "__main__":
	main()
