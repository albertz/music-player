
import sys, os
if sys.platform != "darwin":
	print "GUI: your platform is probably not supported yet"

from guiCocoaCommon import *
from utils import *
import Traits

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

def setupAfterAppFinishedLaunching(delegate):
	from State import state
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
		try:
			from State import modules
			for m in modules: m.start()
			setupAfterAppFinishedLaunching(self)
		except:
			sys.excepthook(*sys.exc_info())

	def applicationShouldTerminate_(self, app):
		print "AppDelegate quit"
		from State import modules
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
	# Note: not needed when bundled...
	mydir = os.path.dirname(__file__)
	icon = NSImage.alloc()
	icon.initWithContentsOfFile_(mydir + "/icon.icns")
	app.setApplicationIconImage_(icon)

	appDelegate = PyAppDelegate.alloc().init()
	app.setDelegate_(appDelegate)
	appDelegate.retain()

	app.finishLaunching()






def buildControlAction(control):
	button = NSButton.alloc().initWithFrame_(((10.0, 10.0), (50.0, 25.0)))
	button.setBezelStyle_(NSRoundedBezelStyle)
	actionTarget = ButtonActionHandler.alloc().initWithArgs(control.attr, control.parent.subjectObject)
	actionTarget.retain() # TODO: where would we release this? ...
	button.setTarget_(actionTarget)
	button.setAction_("click")
	def do_update(): button.setTitle_(control.attr.name.decode("utf-8"))
	do_update()
	button.sizeToFit() # to get height
	button.setFrameSize_((50, button.frame().size.height))
	def update(ev, args, kwargs): do_in_mainthread(do_update, wait=False)
	control.nativeGuiObject = button
	control.updateContent = update
	return control

def buildControlOneLineTextLabel(control):
	label = NSTextField.alloc().initWithFrame_(((10.0, 10.0), (100.0, 22.0)))
	label.setBordered_(False)
	if control.attr.withBorder:
		label.setBezeled_(True)
		label.setBezelStyle_(NSTextFieldRoundedBezel)
	label.setDrawsBackground_(True)
	label.setBackgroundColor_(NSColor.whiteColor())
	label.setEditable_(False)
	label.cell().setUsesSingleLineMode_(True)
	label.cell().setLineBreakMode_(NSLineBreakByTruncatingTail)
	control.nativeGuiObject = label

	def update(ev, args, kwargs):
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		labelContent = control.subjectObject
		s = "???"
		try:
			s = str(labelContent)
			s = s.decode("utf-8")
		except: pass
		def do_update():
			label.setStringValue_(s)
			if any([(c.attr and c.attr.highlight) for c in control.allParents()]):
				label.setBackgroundColor_(NSColor.blueColor())
			if any([(c.attr and c.attr.lowlight) for c in control.allParents()]):
				label.setTextColor_(NSColor.disabledControlTextColor())
			if control.attr.autosizeWidth:
				label.sizeToFit()
				control.layoutLine()
		do_in_mainthread(do_update, wait=False)

	control.updateContent = update
	return control

def buildControlList(control):
	list = control.subjectObject
	scrollview = NSScrollView.alloc().initWithFrame_(((10.0, 10.0), (80.0, 80.0)))
	scrollview.setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	scrollview.contentView().setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	scrollview.setDocumentView_(NSFlippedView.alloc().initWithFrame_(scrollview.contentView().frame()))
	scrollview.documentView().setAutoresizingMask_(NSViewWidthSizable)
	scrollview.setHasVerticalScroller_(True)
	scrollview.setDrawsBackground_(False)
	scrollview.setBorderType_(NSGrooveBorder)
	
	control.nativeGuiObject = scrollview
	control.guiObjectList = [] # all access on this list is done in the main thread
	control.OuterSpace = (0,0)
	control.childIter = lambda: control.guiObjectList
	control.childGuiObjectsInColumn = lambda: control.guiObjectList
	
	@property
	def childIter(self): return self.childs.itervalues()
	
	def doUpdate():
		x,y = 0,0
		for subCtr in control.guiObjectList:
			w = control.innerSize[0]
			h = subCtr.size[1]
			subCtr.pos = (x,y)
			subCtr.size = (w,h)
			y += subCtr.size[1]
		scrollview.documentView().setFrameSize_((scrollview.contentView().bounds().size.width, y))
	def update(): do_in_mainthread(doUpdate, wait=False)
	control.layout = doUpdate
	
	class AttrWrapper:
		def __init__(self, index, value):
			self.index = index
			self.value = value
		def __get__(self, inst):
			return self.value
	def buildControlForIndex(index, value):
		subCtr = CocoaGuiObject()
		subCtr.subjectObject = value
		subCtr.parent = control
		buildControlObject(subCtr)
		subCtr.autoresize = (False,False,True,False)
		scrollview.documentView().addSubview_(subCtr.nativeGuiObject)
		return subCtr
	
	with list.lock:
		control.guiObjectList = [buildControlForIndex(i, list[i]) for i in range(len(list))]
		doUpdate()
		
		def list_onInsert(index, value):
			do_in_mainthread(lambda: control.guiObjectList.insert(index, buildControlForIndex(index, value)), wait=False)
			update()
		def list_onRemove(index):
			def doRemove():
				control.guiObjectList[index].nativeGuiObject.removeFromSuperview()
				del control.guiObjectList[index]
			do_in_mainthread(doRemove, wait=False)			
			update()
		def list_onClear():
			def removeAll():
				for subCtr in control.guiObjectList:
					subCtr.nativeGuiObject.removeFromSuperview()
				del control.guiObjectList[:]
			do_in_mainthread(removeAll, wait=False)
			update()
		
		for ev in ["onInsert","onRemove","onClear"]:
			setattr(list, ev, locals()["list_" + ev])
			
	return control

def buildControlObject(control):
	subview = NSFlippedView.alloc().initWithFrame_(((10.0, 10.0), (80.0, 80.0)))
	control.nativeGuiObject = subview
	control.OuterSpace = (0,0)
	w,h = control.setupChilds()
	control.size = (w,h)
	return control

def SongDisplayView_MouseClickCallback(x):
	from State import state
	song = state.player.curSong
	if not song: return
	if not song.duration: return
	if song.duration < 0: return
	state.player.seekAbs(x * song.duration)

def buildControlSongDisplay(control):
	userAttr = control.attr
	inst = control.parent.subjectObject
	try:
		class SongDisplayView(NSBox):
			def mouseDown_(self, event):
				location = self.convertPoint_fromView_(event.locationInWindow(), None)
				if NSPointInRect(location, self.bounds()):
					x = float(location.x) / self.bounds().size.width
					if x < 0 or x > 1: return
					SongDisplayView_MouseClickCallback(x)
	except:
		SongDisplayView = objc.lookUpClass("SongDisplayView") # already defined earlier

	subview = SongDisplayView.alloc().initWithFrame_(((10.0, 10.0), (80.0, 80.0)))
	subview.setTitlePosition_(NSNoTitle)
	#subview.setContentViewMargins_((0,0))
	imgview = NSImageView.alloc().initWithFrame_(subview.contentView().bounds())
	imgview.setImageScaling_(NSScaleToFit)
	imgview2 = NSImageView.alloc().initWithFrame_(((0,0), (10, subview.contentView().bounds().size.height)))
	imgview2.setImageScaling_(NSScaleToFit)
	subview.contentView().addSubview_(imgview)
	subview.contentView().addSubview_(imgview2)
	imgview.setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	imgview2.setAutoresizingMask_(NSViewHeightSizable|NSViewMinXMargin|NSViewMaxXMargin)

	from threading import Lock
	from State import state

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

		def getBmpData(self):
			better_exchook.install()
			pool = NSAutoreleasePool.alloc().init() # for setSongBitmap

			bmpData = None
			with self.lock:
				if state.player.curSong is not self.curSong: return None
				if getattr(self.curSong, "bmpThumbnail", None):
					bmpData = self.curSong.bmpThumbnail
				else:
					# create song copy for calcBitmapThumbnail
					from Song import Song
					song = Song(url=self.curSong.url)

			if bmpData:
				self.setSongBitmap(bmpData)
				del pool
				return

			do_in_mainthread(lambda: imgview.setImage_(None), wait=False)

			def doBmpCalc(queue):
				try:
					def calcBmpCallback(song, completion, duration, bmpData):
						if subview.window() is None: return False # window was closed
						with self.lock:
							if song != self.curSong: return False
						queue.put((duration, bmpData))
						return True

					song.openFile()
					import ffmpeg
					bmpThumbRet = ffmpeg.calcBitmapThumbnail(song, 600, 81, procCallback = calcBmpCallback)
					if bmpThumbRet:
						queue.put(bmpThumbRet)
				except:
					print "doBmpCalc raised exception"
					sys.excepthook(*sys.exc_info())
				queue.put(None)
			from multiprocessing import Process, Queue
			queue = Queue()
			Process(target=doBmpCalc, args=(queue,)).start()

			while True:
				bmpThumbRet = queue.get()
				if bmpThumbRet is None: break

				duration, bmpData = bmpThumbRet

				with self.lock:
					self.curSong.duration = duration
					self.curSong.bmpThumbnail = bmpData
				self.setSongBitmap(bmpData, wait=False)

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
				control.parent.childs["curSongPos"].updateContent(None,None,None)

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

	control.nativeGuiObject = subview
	control.updateContent = songDisplay.update	
	return control


def buildControl(userAttr, parent):
	control = CocoaGuiObject()
	control.parent = parent
	control.attr = userAttr
	control.subjectObject = userAttr.__get__(parent.subjectObject)
	if userAttr.isType(Traits.Action):
		return buildControlAction(control)
	elif userAttr.isType(Traits.OneLineText):
		if userAttr.writeable:
			raise NotImplementedError
		else:
			return buildControlOneLineTextLabel(control)
	elif userAttr.isType(Traits.Enum):
		raise NotImplementedError
	elif userAttr.isType(Traits.List):
		return buildControlList(control)
	elif userAttr.isType(Traits.Object):
		return buildControlObject(control)
	elif userAttr.isType(Traits.SongDisplay):
		return buildControlSongDisplay(control)
	else:
		raise NotImplementedError, "%r not handled yet" % userAttr.type

window = None

class CocoaGuiObject(object):
	def __init__(self):
		# Do that late because we cannot import gui globally here. (circular dep)
		import gui
		self.__class__.__bases__ = (gui.GuiObject, object)
	
	nativeGuiObject = None
	
	@property
	def pos(self): return (self.nativeGuiObject.frame().origin.x, self.nativeGuiObject.frame().origin.y)	
	@pos.setter
	def pos(self, value): self.nativeGuiObject.setFrameOrigin_(value)
	@property
	def size(self): return (self.nativeGuiObject.frame().size.width, self.nativeGuiObject.frame().size.height)
	@size.setter
	def size(self, value): self.nativeGuiObject.setFrameSize_(value)
	@property
	def innerSize(self): return (self.nativeGuiObject.bounds().size.width, self.nativeGuiObject.bounds().size.height)

	@property
	def autoresize(self):
		flags = self.nativeGuiObject.autoresizingMask()
		return (flags & NSViewMinXMargin, flags & NSViewMinYMargin, flags & NSViewWidthSizable, flags & NSViewHeightSizable)
	@autoresize.setter
	def autoresize(self, value):
		flags = 0
		if value[0]: flags |= NSViewMinXMargin
		if value[1]: flags |= NSViewMinYMargin
		if value[2]: flags |= NSViewWidthSizable
		if value[3]: flags |= NSViewHeightSizable
		self.nativeGuiObject.setAutoresizingMask_(flags)
		
	def addChild(self, child):
		self.nativeGuiObject.addSubview_(child.nativeGuiObject)
		
def setupWindow():
	# some example code: http://lists.apple.com/archives/cocoa-dev/2004/Jan/msg01389.html
	# also, these might be helpful:
	# https://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/ControlCell/ControlCell.html#//apple_ref/doc/uid/10000015i
	# http://cocoadev.com/wiki/FlowLayoutView

	assert NSThread.isMainThread()

	win = NSWindow.alloc()
	win.initWithContentRect_styleMask_backing_defer_(
		((200.0, 500.0), (400.0, 600.0)),
		NSTitledWindowMask |
		NSClosableWindowMask |
		NSMiniaturizableWindowMask |
		NSResizableWindowMask,
		NSBackingStoreBuffered, False)
	win.setContentView_(NSFlippedView.alloc().init())
	win.contentView().setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	
	import appinfo
	win.setTitle_(appinfo.progname)

	from State import state
	global window
	window = CocoaGuiObject()
	window.subjectObject = state
	window.nativeGuiObject = win.contentView()
	w,h = window.setupChilds()

	win.setContentMinSize_((w,h))
	
	win.display()
	win.orderFrontRegardless()
	win.makeMainWindow()
	win.makeKeyWindow()
	
	win.center() # later: restore earlier pos/size

	app.activateIgnoringOtherApps_(True)
	# see http://stackoverflow.com/questions/12292151/crash-in-class-getname-in-applicationopenuntitledfile
	win.retain()






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
	global window
	window = None
	
	appDelegate = PyAppDelegate.alloc().init()
	app.setDelegate_(appDelegate)
	appDelegate.retain()

	try:
		setupAfterAppFinishedLaunching(appDelegate)
	except:
		sys.excepthook(*sys.exc_info())

def guiMain():
	pool = NSAutoreleasePool.alloc().init()
	from State import state
	for ev,args,kwargs in state.updates.read():
		try:
			global window
			if window:
				window.updateContent(ev,args,kwargs)
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

