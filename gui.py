
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
import appinfo

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

import Traits

def buildControlAction(userAttr, inst):
	button = NSButton.alloc().initWithFrame_(((10.0, 10.0), (80.0, 80.0)))
	button.setTitle_(userAttr.name)
	button.setBezelStyle_(2)
	try:
		class ButtonActionHandler(NSObject):
			def initWithArgs(self, userAttr, inst):
				self.init()
				self.userAttr = userAttr
				self.inst = inst
				return self
			def click(self, sender):
				print "click!!", sender, self.userAttr
				attr = self.userAttr.__get__(self.inst)
				attr()
	except:
		ButtonActionHandler = objc.lookUpClass("ButtonActionHandler") # already defined earlier
	actionTarget = ButtonActionHandler.alloc().initWithArgs(userAttr, inst)
	actionTarget.retain() # TODO: where would we release this? ...
	button.setTarget_(actionTarget)
	button.setAction_("click")
	return button

def buildControlOneLineTextLabel(userAttr, inst):
	label = NSTextField.alloc().initWithFrame_(((10.0, 10.0), (80.0, 80.0)))
	label.setEditable_(False)
	return label

def buildControlEnum(userAttr, inst):
	# TODO
	return buildControlOneLineTextLabel(userAttr, inst)

def buildControlList(userAttr, inst):
	# TODO
	return buildControlOneLineTextLabel(userAttr, inst)

def buildControl(userAttr, inst):
	def isType(T):
		try: return issubclass(userAttr.type, T)
		except TypeError: return isinstance(userAttr.type, T)
	control = None
	if isType(Traits.Action):
		control = buildControlAction(userAttr, inst)
	elif isType(Traits.OneLineText):
		if userAttr.writeable:
			raise NotImplementedError
		else:
			control = buildControlOneLineTextLabel(userAttr, inst)
	elif isType(Traits.Enum):
		control = buildControlEnum(userAttr, inst)
	elif isType(Traits.List):
		control = buildControlList(userAttr, inst)
	else:
		raise NotImplementedError, "%r not handled yet" % userAttr.type
	assert control
	return control

def setupWindow():
	# some example code: http://lists.apple.com/archives/cocoa-dev/2004/Jan/msg01389.html
	# also, these might be helpful:
	# https://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/ControlCell/ControlCell.html#//apple_ref/doc/uid/10000015i
	# http://cocoadev.com/wiki/FlowLayoutView

	w = NSWindow.alloc()
	w.initWithContentRect_styleMask_backing_defer_(
		((200.0, 200.0), (250.0, 100.0)),
		NSTitledWindowMask |
		NSClosableWindowMask |
		NSMiniaturizableWindowMask |
		NSResizableWindowMask,
		NSBackingStoreBuffered, False)
	w.setTitle_(appinfo.progname)

	x = 0
	y = 0
	for attr in iterUserAttribs(state):
		print attr
		control = buildControl(attr, state)
		control.setFrameOrigin_((x,y))
		y += 100
		w.contentView().addSubview_(control)

	w.display()
	w.orderFrontRegardless()
	w.makeMainWindow()
	w.makeKeyWindow()

	app.activateIgnoringOtherApps_(True)
	# see http://stackoverflow.com/questions/12292151/crash-in-class-getname-in-applicationopenuntitledfile
	w.retain()

def setupAfterAppFinishedLaunching(delegate):
	state.quit = quit
	setupAppleMenu()
	setupWindow()
	app.updateWindows()
	print "setupAfterAppFinishedLaunching ready"

class PyAppDelegate(NSObject):
	__metaclass__ = ObjCClassAutorenamer

	# Doc for AppDelegate protocol:
	# https://developer.apple.com/library/mac/#documentation/Cocoa/Reference/NSApplicationDelegate_Protocol/Reference/Reference.html

	def applicationDidFinishLaunching_(self, notification):
		print "AppDelegate didFinishLaunching"
		for m in modules: m.start()
		try:
			setupAfterAppFinishedLaunching(self)
		except:
			sys.excepthook(*sys.exc_info())

	def applicationShouldTerminate_(self, app):
		print "AppDelegate quit"
		for m in modules: m.stop()
		return NSTerminateNow

	def applicationOpenUntitledFile_(self, app):
		setupWindow()
		return True

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

try:
	isReload
except NameError:
	isReload = False
else:
	isReload = True

def reloadModuleHandling():
	print "GUI module reload handler ..."

	for w in app.windows():
		w.close()

	appDelegate = PyAppDelegate.alloc().init()
	app.setDelegate_(appDelegate)
	appDelegate.retain()

	try:
		setupAfterAppFinishedLaunching(appDelegate)
	except:
		sys.excepthook(*sys.exc_info())

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
