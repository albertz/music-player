
import sys
if sys.platform != "darwin":
	print "GUI: your platform is probably not supported yet"
	def guiMain(): pass

import objc
from Foundation import *
from AppKit import *
import os, sys
from State import state, modules

mydir = os.path.dirname(__file__) or os.getcwd()
app = None

def setupAppleMenu():

	# http://www.cocoabuilder.com/archive/cocoa/192181-initializing-the-menubar-without-interface-builder.html

	mainMenu = NSMenu.alloc().initWithTitle_("MainMenu")
	mi = mainMenu.addItemWithTitle_action_keyEquivalent_("Apple", None, "")
	m = NSMenu.alloc().initWithTitle_("Apple")

	# strange hack
	app.setAppleMenu_(m)
	mainMenu.setSubmenu_forItem_(m, mi)
	mi = m.addItemWithTitle_action_keyEquivalent_('Quit', 'terminate:', 'q')

	app.setMainMenu_(mainMenu)
	return

	menu = NSMenu.alloc().init()
	app.setMainMenu_(menu)

	# Comment from SDLmain.m where this code comes from:
	# yes, we do need to add it and then remove it --
	# if you don't add it, it doesn't get displayed
	# if you don't remove it, you have an extra, titleless item in the menubar
	# when you remove it, it appears to stick around
	# very, very odd

	#appleMenuController = NSAppleMenuController.alloc().init()
	#appleMenuController.retain()

	appleMenu = NSMenu.alloc().initWithTitle_('MainMenu')

	menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', 'q')
	appleMenu.addItem_(menuitem)

	appleMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('', None, '')
	appleMenuItem.setSubmenu_(appleMenu)

	app.mainMenu().addItem_(appleMenuItem)

	#appleMenuController.controlMenu_(appleMenu)
	#app.mainMenu().removeItem_(appleMenuItem)

	#app.setAppleMenu_(appleMenu)
	#app.setAppleMenu_(appleMenuItem)

	print appleMenu


	#print menu
	print app.mainMenu()

	return

class PyAppDelegate(NSObject):
	def applicationDidFinishLaunching_(self, notification):
		print "AppDelegate didFinishLaunching"
		#statusbar = NSStatusBar.systemStatusBar()
		#self.statusitem = statusbar.statusItemWithLength_(NSVariableStatusItemLength)
		#self.statusitem.setHighlightMode_(1)
		#self.statusitem.setToolTip_('Example')
		#self.statusitem.setTitle_('Example')

		setupAppleMenu()
		#self.statusitem.setMenu_(self.menu)

		state.quit = quit

		for m in modules: m.start()

	def applicationShouldTerminate_(self, app):
		print "AppDelegate quit"

		for m in modules: m.stop()
		return NSTerminateNow

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
	assert NSThread.isMainThread()
	global app

	app = NSApplication.sharedApplication()
	setup()

	print "entering GUI main loop"
	app.run()

	sys.exit()

if __name__ == "__main__":
	main()
