
import sys
if sys.platform != "darwin":
	print "GUI: your platform is probably not supported yet"
	def guiMain(): pass

import objc
from AppKit import *
import os, sys
from State import state, modules

mydir = os.path.dirname(__file__) or os.getcwd()
app = None

class AppDelegate(NSObject):
	def applicationDidFinishLaunching_(self, notification):
		print "AppDelegate didFinishLaunching"
		statusbar = NSStatusBar.systemStatusBar()
		self.statusitem = statusbar.statusItemWithLength_(NSVariableStatusItemLength)
		self.statusitem.setHighlightMode_(1)
		self.statusitem.setToolTip_('Example')
		self.statusitem.setTitle_('Example')

		self.menu = NSMenu.alloc().init()
		menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
		self.menu.addItem_(menuitem)
		self.statusitem.setMenu_(self.menu)

		for m in modules: m.start()

	def applicationShouldTerminate_(self, app):
		print "AppDelegate quit"

		for m in modules: m.stop()

def setup():
	icon = NSImage.alloc()
	icon.initWithContentsOfFile_(mydir + "/icon.icns")
	app.setApplicationIconImage_(icon)

	appDelegate = AppDelegate.alloc().init()
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
	#app.run()
	#app.performSelectorOnMainThread_withObject_waitUntilDone_(app.run, None, False)
	app.run()

	sys.exit()

if __name__ == "__main__":
	main()
