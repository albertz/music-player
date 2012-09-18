
import sys
from player import PlayerEventCallbacks

if sys.platform != "darwin":
	print "GUI: your platform is probably not supported yet"

import objc
from AppKit import *
from collections import deque

try: pools
except NameError: pools = deque()

# just in case that we are not the main thread
pools.append(NSAutoreleasePool.alloc().init())

import os
from Song import Song
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
	button = NSButton.alloc().initWithFrame_(((10.0, 10.0), (50.0, 30.0)))
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
				from threading import Thread
				Thread(target=attr, name="click handler").start()
	except:
		ButtonActionHandler = objc.lookUpClass("ButtonActionHandler") # already defined earlier
	actionTarget = ButtonActionHandler.alloc().initWithArgs(userAttr, inst)
	actionTarget.retain() # TODO: where would we release this? ...
	button.setTarget_(actionTarget)
	button.setAction_("click")
	def update(ev, args, kwargs):
		do_in_mainthread(lambda : button.setTitle_(userAttr.name.decode("utf-8")), wait=False)
	return button, update

def buildControlOneLineTextLabel(userAttr, inst):
	label = NSTextField.alloc().initWithFrame_(((10.0, 10.0), (100.0, 25.0)))
	label.setBordered_(False)
	label.setBezeled_(True)
	#label.setDrawsBackground_(False)
	label.setEditable_(False)
	label.cell().setLineBreakMode_(NSLineBreakByTruncatingTail)
	def update(ev, args, kwargs):
		labelContent = userAttr.__get__(inst)
		s = "???"
		try:
			s = str(labelContent)
			s = s.decode("utf-8")
		except: pass
		do_in_mainthread(lambda: label.setStringValue_(s), wait=False)
	return label, update

def buildControlList(userAttr, inst):
	subview = NSBox.alloc().initWithFrame_(((10.0, 10.0), (80.0, 80.0)))
	subview.setTitle_(userAttr.name.decode("utf-8"))
	def update(ev, args, kwargs):
		pass
	return subview, update

def buildControlObject(userAttr, inst):
	subview = NSBox.alloc().initWithFrame_(((10.0, 10.0), (80.0, 80.0)))
	subview.setTitle_(userAttr.name.decode("utf-8"))
	def update(ev, args, kwargs):
		pass
	return subview, update

def SongDisplayView_MouseClickCallback(x):
	song = state.player.curSong
	if not song: return
	if not song.duration: return
	if song.duration < 0: return
	state.player.seekAbs(x * song.duration)

def buildControlSongDisplay(userAttr, inst):
	try:
		class SongDisplayView(NSView):
			def mouseDown_(self, event):
				location = self.convertPoint_fromView_(event.locationInWindow(), None)
				if NSPointInRect(location, self.bounds()):
					x = float(location.x) / self.bounds().size.width
					if x < 0 or x > 1: return
					SongDisplayView_MouseClickCallback(x)
	except:
		SongDisplayView = objc.lookUpClass("SongDisplayView") # already defined earlier

	subview = SongDisplayView.alloc().initWithFrame_(((10.0, 10.0), (80.0, 80.0)))
	imgview = NSImageView.alloc().initWithFrame_(((0.0, 0.0), (80.0, 80.0)))
	imgview.setImageScaling_(NSScaleToFit)
	imgview2 = NSImageView.alloc().initWithFrame_(((0.0, 0.0), (10.0, 80.0)))
	imgview2.setImageScaling_(NSScaleToFit)
	subview.addSubview_(imgview)
	subview.addSubview_(imgview2)
	imgview.setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	imgview2.setAutoresizingMask_(NSViewHeightSizable|NSViewMinXMargin|NSViewMaxXMargin)

	from threading import Lock

	class SongDisplay:
		def __init__(self):
			self.lock = Lock()
			self.curSong = None

		def initSongCursorImg(self):
			img2 = NSImage.alloc().initWithSize_((5,1))
			img2.lockFocus()
			for i in range(5):
				a = 100 - abs(i - 2) * 50
				NSColor.colorWithDeviceRed_green_blue_alpha_(0.0,0.0,0.0,a).setFill()
				NSBezierPath.fillRect_(((i,0),(1,1)))
			img2.unlockFocus()
			do_in_mainthread(lambda: imgview2.setImage_(img2))

		def setSongBitmap(self, bmpData, wait=True):
			with self.lock:
				if state.player.curSong is not self.curSong: return None
			data = NSData.alloc().initWithBytes_length_(bmpData, len(bmpData))
			img = NSImage.alloc().initWithData_(data)
			do_in_mainthread(lambda: imgview.setImage_(img), wait=wait)

		def calcBmpCallback(self, song, completion, duration, bmpData):
			if subview.window() is None: return False # window was closed
			with self.lock:
				if song != self.curSong: return False
				self.curSong.duration = duration
			self.setSongBitmap(bmpData, wait=False)
			return True

		def getBmpData(self):
			better_exchook.install()
			pool = NSAutoreleasePool.alloc().init() # for setSongBitmap

			bmpData = None
			with self.lock:
				if state.player.curSong is not self.curSong: return None
				if self.curSong.bmpThumbnail:
					bmpData = self.curSong.bmpThumbnail
				else:
					# create song copy for calcBitmapThumbnail
					song = Song(url=self.curSong.url)

			if bmpData:
				self.setSongBitmap(self.curSong.bmpThumbnail)
				del pool
				return

			do_in_mainthread(lambda: imgview.setImage_(None), wait=False)

			song.openFile()
			import ffmpeg
			bmpThumbRet = ffmpeg.calcBitmapThumbnail(song, 600, 81, procCallback = self.calcBmpCallback)
			if bmpThumbRet:
				duration, bmpData = bmpThumbRet

				with self.lock:
					self.curSong.duration = duration
					self.curSong.bmpThumbnail = bmpData
				self.setSongBitmap(bmpData)

			del pool

		def playCursorUpdater(self):
			better_exchook.install()
			pool = NSAutoreleasePool.alloc().init()

			def updateCursor():
				with self.lock:
					if self.curSong is None: return
					if state.player.curSong is not self.curSong: return
					w = imgview2.frame().size.width
					h = imgview2.frame().size.height
					x = subview.bounds().size.width * state.player.curSongPos / self.curSong.duration - w / 2
					y = imgview2.frame().origin.y
					imgview2.setFrame_(((x,y),(w,h)))

			import time
			i = 0
			while True:
				i += 1
				time.sleep(0.1)
				if subview.window() is None: return # window was closed
				with self.lock:
					if self.curSong is None: continue
					if self.curSong is not state.player.curSong: continue
				do_in_mainthread(updateCursor, wait=False)

				# another hack: update time
				updateHandlers["curSongPos"](None,None,None)

			del pool

		def update(self, ev, args, kwargs):
			#if ev is PlayerEventCallbacks.onSongChange:
			with self.lock:
				if self.curSong is state.player.curSong: return # song not changed
				self.curSong = state.player.curSong

			if not self.curSong:
				do_in_mainthread(lambda: imgview.setImage_(None), wait=False)
				return

			from threading import Thread
			Thread(target=self.getBmpData, name="GUI song bitmap loader").start()

	songDisplay = SongDisplay()
	songDisplay.initSongCursorImg()
	Thread(target=songDisplay.playCursorUpdater, name="GUI play cursor updater").start()

	return subview, songDisplay.update

def buildControl(userAttr, inst):
	if userAttr.isType(Traits.Action):
		return buildControlAction(userAttr, inst)
	elif userAttr.isType(Traits.OneLineText):
		if userAttr.writeable:
			raise NotImplementedError
		else:
			return buildControlOneLineTextLabel(userAttr, inst)
	elif userAttr.isType(Traits.Enum):
		raise NotImplementedError
	elif userAttr.isType(Traits.List):
		return buildControlList(userAttr, inst)
	elif userAttr.isType(Traits.Object):
		return buildControlObject(userAttr, inst)
	elif userAttr.isType(Traits.SongDisplay):
		return buildControlSongDisplay(userAttr, inst)
	else:
		raise NotImplementedError, "%r not handled yet" % userAttr.type

def setupWindow():
	assert NSThread.isMainThread()
	# some example code: http://lists.apple.com/archives/cocoa-dev/2004/Jan/msg01389.html
	# also, these might be helpful:
	# https://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/ControlCell/ControlCell.html#//apple_ref/doc/uid/10000015i
	# http://cocoadev.com/wiki/FlowLayoutView

	win = NSWindow.alloc()
	win.initWithContentRect_styleMask_backing_defer_(
		((200.0, 500.0), (500.0, 400.0)),
		NSTitledWindowMask |
		NSClosableWindowMask |
		NSMiniaturizableWindowMask |
		NSResizableWindowMask,
		NSBackingStoreBuffered, False)
	win.setTitle_(appinfo.progname)

	try:
		class NSFlippedView(NSView):
			def isFlipped(self): return True
	except:
		NSFlippedView = objc.lookUpClass("NSFlippedView")
	win.setContentView_(NSFlippedView.alloc().init())

	global updateHandlers
	updateHandlers = {} # map attrName -> functions (ev,args,kwargs -> ?)
	global guiHandleUpdate
	def guiHandleUpdate(ev,args,kwargs):
		for attrName,handleFunc in updateHandlers.items():
			handleFunc(ev,args,kwargs)

	defaultSpaceX, defaultSpaceY = 8, 8
	x, y = defaultSpaceX, defaultSpaceY
	maxY = 0
	lastControl = None
	lastHorizControls = []

	def finishLastHoriz():
		if not lastControl: return
		varWidthControl = None
		for attr,control in lastHorizControls:
			if attr.variableWidth:
				varWidthControl = control
				break
		if not varWidthControl:
			varWidthControl = lastControl
		x = win.contentView().bounds().size.width
		for attr,control in reversed(lastHorizControls):
			w = control.frame().size.width
			h = control.frame().size.height
			y = control.frame().origin.y

			if control is varWidthControl:
				w = x - control.frame().origin.x - defaultSpaceY
				x = control.frame().origin.x
				control.setFrame_(((x,y),(w,h)))
				control.setAutoresizingMask_(NSViewWidthSizable)
				break
			else:
				x -= w + defaultSpaceY
				control.setFrame_(((x,y),(w,h)))
				control.setAutoresizingMask_(NSViewMinXMargin)

	def finishLastVert():
		if lastControl:
			h = lastControl.frame().origin.y + lastControl.frame().size.height + defaultSpaceY
			win.setContentMinSize_((250.0,h))

			# make the last one vertically resizable
			h = win.contentView().bounds().size.height - y - defaultSpaceY
			w = win.contentView().bounds().size.width - defaultSpaceY * 2
			lastControl.setFrame_(((x,y),(w,h)))
			lastControl.setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)

	for attr in iterUserAttribs(state):
		print attr
		control, update = buildControl(attr, state)
		# Note: Avoid NSLayoutConstraint as this is >=10.7.
		# We can easily make this whole GUI working for earlier MacOSX versions.
		win.contentView().addSubview_(control)

		if attr.alignRight and lastControl: # align next right
			x = lastControl.frame().origin.x + lastControl.frame().size.width + defaultSpaceX
			# y from before
			w = control.frame().size.width # default
			h = control.frame().size.height # default

		else: # align next below
			finishLastHoriz()
			lastHorizControls = []
			x = defaultSpaceX
			y = maxY + defaultSpaceY
			w = control.frame().size.width # default
			h = control.frame().size.height # default

		control.setFrame_(((x,y),(w,h)))
		control.setAutoresizingMask_(0)

		lastControl = control
		lastHorizControls += [(attr,control)]
		maxY = max(maxY, control.frame().origin.y + control.frame().size.height)

		update(None,None,None)

		if attr.updateHandler:
			def handleFunc(ev,args,kwargs,attr=attr,update=update):
				try:
					attr.updateHandler(state, attr, ev, args, kwargs)
				except:
					sys.excepthook(*sys.exc_info())
				update(ev, args, kwargs)
			updateHandlers[attr.name] = handleFunc

	finishLastHoriz()
	finishLastVert()

	win.display()
	win.orderFrontRegardless()
	win.makeMainWindow()
	win.makeKeyWindow()

	app.activateIgnoringOtherApps_(True)
	# see http://stackoverflow.com/questions/12292151/crash-in-class-getname-in-applicationopenuntitledfile
	win.retain()

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

# This function will get overridden by setupWindow().
def guiHandleUpdate(*args): pass

def guiMain():
	pool = NSAutoreleasePool.alloc().init()
	for ev,args,kwargs in state.updates.read():
		try:
			guiHandleUpdate(ev, args, kwargs)
		except:
			sys.excepthook(*sys.exc_info())
	del pool

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
