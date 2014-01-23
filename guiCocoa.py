# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import sys, os
if sys.platform != "darwin":
	print "GUI: your platform is probably not supported yet"

from _guiCocoa import *
from guiCocoaCommon import *
from utils import *
from weakref import ref
import Traits


def setupAppleMenu():

	# http://www.cocoabuilder.com/archive/cocoa/192181-initializing-the-menubar-without-interface-builder.html
	# By Robert Nikander

	mainMenu = AppKit.NSMenu.alloc().initWithTitle_("MainMenu")
	mi = mainMenu.addItemWithTitle_action_keyEquivalent_("Apple", None, "")
	m = AppKit.NSMenu.alloc().initWithTitle_("Apple")

	# strange hack
	AppKit.NSApp.setAppleMenu_(m)
	mainMenu.setSubmenu_forItem_(m, mi)
	
	m.addItemWithTitle_action_keyEquivalent_('About MusicPlayer', 'about:', '')
	m.addItem_(AppKit.NSMenuItem.separatorItem())
	m.addItemWithTitle_action_keyEquivalent_('Hide MusicPlayer', 'hide:', 'h')
	mii = m.addItemWithTitle_action_keyEquivalent_('Hide Others', 'hideOtherApplications:', 'h')
	mii.setKeyEquivalentModifierMask_(AppKit.NSAlternateKeyMask|AppKit.NSCommandKeyMask)
	m.addItemWithTitle_action_keyEquivalent_('Show All', 'unhideAllApplications:', '')
	m.addItem_(AppKit.NSMenuItem.separatorItem())
	m.addItemWithTitle_action_keyEquivalent_('Quit', 'terminate:', 'q')

	# new supermenu
	mi = mainMenu.addItemWithTitle_action_keyEquivalent_("Edit", None, "")
	m = AppKit.NSMenu.alloc().initWithTitle_("Edit")
	mainMenu.setSubmenu_forItem_(m, mi)

	m.addItemWithTitle_action_keyEquivalent_('Cut', 'cut:', 'x')
	m.addItemWithTitle_action_keyEquivalent_('Copy', 'copy:', 'c')
	m.addItemWithTitle_action_keyEquivalent_('Paste', 'paste:', 'v')
	m.addItemWithTitle_action_keyEquivalent_('Select all', 'selectText:', 'a')

	# new supermenu
	mi = mainMenu.addItemWithTitle_action_keyEquivalent_("Window", None, "")
	m = AppKit.NSMenu.alloc().initWithTitle_("Window")
	mainMenu.setSubmenu_forItem_(m, mi)

	m.addItemWithTitle_action_keyEquivalent_('Main window', 'openMainWindow:', '1')
	m.addItemWithTitle_action_keyEquivalent_('Search window', 'openSearchWindow:', '2')
	m.addItemWithTitle_action_keyEquivalent_('Song edit window', 'openSongEditWindow:', 'i')
	m.addItem_(AppKit.NSMenuItem.separatorItem())
	m.addItemWithTitle_action_keyEquivalent_('Minimize window', 'miniaturize:', 'm')
	m.addItemWithTitle_action_keyEquivalent_('Close window', 'performClose:', 'w')		

	# new supermenu
	mi = mainMenu.addItemWithTitle_action_keyEquivalent_("Control", None, "")
	m = AppKit.NSMenu.alloc().initWithTitle_("Control")
	mainMenu.setSubmenu_forItem_(m, mi)

	m.addItemWithTitle_action_keyEquivalent_('no song yet', '', '')
	m.addItemWithTitle_action_keyEquivalent_('Play', 'playPause:', '')
	m.addItemWithTitle_action_keyEquivalent_('Next song', 'nextSong:', '')
	
	AppKit.NSApp.delegate().setDockMenu_(m)
	AppKit.NSApp.setDockMenu_(m)

	# new supermenu
	mi = mainMenu.addItemWithTitle_action_keyEquivalent_("Debug", None, "")
	m = AppKit.NSMenu.alloc().initWithTitle_("Debug")
	mainMenu.setSubmenu_forItem_(m, mi)

	m.addItemWithTitle_action_keyEquivalent_('reset player', 'resetPlayer:', '')

	AppKit.NSApp.setMainMenu_(mainMenu)

def setupAfterAppFinishedLaunching():
	from State import modules
	for m in modules: m.start()

	setupAppleMenu()
	setupMainWindow()
	AppKit.NSApp.updateWindows()

	import main
	main.successStartup = True
	print "setupAfterAppFinishedLaunching ready"

def handleApplicationQuit():
	from State import modules
	utils.quit = True
	# first set/send signals to all modules
	for m in modules: m.stop(join=False)
	try:
		# in case there are any subprocesses, interrupt them
		# maybe some modules are hanging and waiting for such
		import sys, os, signal
		os.kill(0, signal.SIGINT)
	except Exception: pass
	# now join all
	for m in modules: m.stop()
	print "Bye!"


def getWindow(name):
	global windows
	if windows.get(name, None):
		return windows[name].nativeGuiObject.window()
	return None



def buildControlAction(control):
	button = AppKit.NSButton.alloc().initWithFrame_(((0,0), (50.0, 25.0)))
	button.setBezelStyle_(AppKit.NSRoundedBezelStyle)
	actionTarget = ButtonActionHandler.alloc().initWithArgs(control.attr, control.parent.subjectObject)
	control.buttonActionHandler = actionTarget # keep ref here. button.target() is only a weakref
	button.setTarget_(actionTarget)
	button.setAction_("click")
	def do_update(): button.setTitle_(control.attr.name.decode("utf-8"))
	do_update()
	button.sizeToFit() # to get height
	#button.setFrameSize_((50, button.frame().size.height))
	def update(): do_in_mainthread(do_update, wait=False)
	control.nativeGuiObject = button
	control.updateContent = update
	return control


def backgroundColor(control):
	if any([(c.attr and c.attr.highlight) for c in control.allParents()]):
		return AppKit.NSColor.blueColor()
	return None

def foregroundColor(control):
	if any([(c.attr and c.attr.lowlight) for c in control.allParents()]):
		return AppKit.NSColor.disabledControlTextColor()
	return AppKit.NSColor.blackColor()


def buildControlClickableLabel(control):
	buildControlOneLineText(control)
	control.getTextObj = lambda: control.subjectObject(handleClick=False)

	label = control.nativeGuiObject
	def onMouseEntered(ev):
		if label.backgroundColor() == AppKit.NSColor.blueColor():
			label.setTextColor_(AppKit.NSColor.grayColor())
		else:
			label.setTextColor_(AppKit.NSColor.blueColor())
	label.onMouseEntered = onMouseEntered
	label.onMouseExited = lambda ev: label.setTextColor_(foregroundColor(control))
	def onMouseDown(ev):
		try:
			control.subjectObject(handleClick=True)
		except Exception:
			sys.excepthook(*sys.exc_info())			
		control.parent.updateContent()
	label.onMouseDown = onMouseDown

	return control

def buildControlEditableText(control):
	label = NSExtendedTextField.alloc().initWithFrame_(((0, 0), (30.0, 22.0)))
	if control.attr.searchLook:
		label.setCell_(AppKit.NSSearchFieldCell.alloc().init())
	label.setBordered_(False)
	label.setBezeled_(True)
	label.setBezelStyle_(AppKit.NSTextFieldRoundedBezel)
	label.setDrawsBackground_(True)
	label.setEditable_(True)
	label.cell().setUsesSingleLineMode_(True)
	#label.cell().setLineBreakMode_(NSLineBreakByTruncatingTail)
	control.nativeGuiObject = label
	control.getTextObj = lambda: control.subjectObject()
	
	def update():
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		s = "???"
		try:
			labelContent = control.getTextObj()
			s = convertToUnicode(labelContent)
		except Exception:
			sys.excepthook(*sys.exc_info())			
		def do_update():
			label.setStringValue_(s)

		do_in_mainthread(do_update, wait=False)

	control.updateContent = update

	def onTextChange():
		try:
			control.subjectObject = control.attr.__get__(control.parent.subjectObject)
			newText = unicode(label.stringValue())
			control.subjectObject(updateText = newText)
		except Exception:
			sys.excepthook(*sys.exc_info())
			
	label.onTextChange = onTextChange

	return control


# used by buildControlList for the list items
class ListItem_AttrWrapper(UserAttrib):
	def __init__(self, index, value, parent):
		UserAttrib.__init__(self)
		self.index = index
		self.value = value
	def __get__(self, inst):
		return self.value


def buildControlTable(control):
	scrollview = AppKit.NSScrollView.alloc().initWithFrame_(((0.0, 0.0), (80.0, 80.0)))
	scrollview.setAutoresizingMask_(AppKit.NSViewWidthSizable|AppKit.NSViewHeightSizable)
	scrollview.contentView().setAutoresizingMask_(AppKit.NSViewWidthSizable|AppKit.NSViewHeightSizable)
	scrollview.setHasVerticalScroller_(True)
	scrollview.setDrawsBackground_(False)
	scrollview.setBorderType_(AppKit.NSBezelBorder)
	
	view = NSFlippedView.alloc().initWithFrame_(scrollview.frame())
	view.setAutoresizingMask_(AppKit.NSViewWidthSizable|AppKit.NSViewHeightSizable)
	view.addSubview_(scrollview)
	view.control = ref(control)
	control.nativeGuiObject = view

	table = AppKit.NSTableView.alloc().initWithFrame_(((0,0),(80,80)))
	scrollview.setDocumentView_(table)
	scrollview.documentView().setAutoresizingMask_(AppKit.NSViewWidthSizable)
	
	#array = NSArrayController.alloc().init()
	dataSource = TableViewDataSource.alloc().init()
	dataSource.data = []
	dataSource.formaters = control.attr.type.formaters
	control.tableDataSource = dataSource # save ref here because table.dataSource() is only a weakref
	table.setDataSource_(dataSource)
	
	if control.attr.selectionChangeHandler:
		delegate = TableViewDelegate.alloc().init()
		delegate.onSelectionChange = lambda sel: control.attr.selectionChangeHandler(control.parent.subjectObject, sel)
		control.tableDelegate = delegate
		table.setDelegate_(delegate)
	
	table.setColumnAutoresizingStyle_(AppKit.NSTableViewUniformColumnAutoresizingStyle)
	for key in control.attr.type.keys:
		column = AppKit.NSTableColumn.alloc().initWithIdentifier_(key)
		column.headerCell().setStringValue_(convertToUnicode(key.capitalize())) # title
		column.setEditable_(False)
		column.setMinWidth_(30)
		column.setSortDescriptorPrototype_(AppKit.NSSortDescriptor.sortDescriptorWithKey_ascending_(key, True))
		table.addTableColumn_(column)
	
	table.setAllowsMultipleSelection_(True)	
	table.setAutosaveName_(control.name)
	table.setAutosaveTableColumns_(True)

	def update():
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		value = control.subjectObject
		def setData():
			with dataSource.lock:
				# Do this in main thread to workaround the problem that
				# the tableView knows the wrong number of rows. This could
				# happen otherwise because it checks the number of rows in
				# its redrawing code and that is not covered by this lock.
				# See also the related comment in TableViewDataSource.
				dataSource.data = value
				dataSource.resort(table) # initial sort
			table.reloadData()
		do_in_mainthread(setData, wait=False)
	control.updateContent = update
	update() # initial fill
	
	return control

def buildControlReal(control):
	w,h = control.attr.width, control.attr.height
	if not w: w = 70
	if not h: h = 20
	slider = NSExtendedSlider.alloc().initWithFrame_(((0.0, 0.0), (w, h)))
	slider.setMinValue_(control.attr.type.min)
	slider.setMaxValue_(control.attr.type.max)
	slider.setNumberOfTickMarks_(3)
	control.nativeGuiObject = slider

	def update():
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		value = control.subjectObject
		do_in_mainthread(lambda: slider.setDoubleValue_(value), wait=False)
	control.updateContent = update

	def onValueChange(newValue):
		control.attr.__set__(control.parent.subjectObject, newValue)	
	slider.onValueChange = onValueChange
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
		class SongDisplayView(AppKit.NSBox):
			def mouseDown_(self, event):
				location = self.convertPoint_fromView_(event.locationInWindow(), None)
				if AppKit.NSPointInRect(location, self.bounds()):
					x = float(location.x) / self.bounds().size.width
					if x < 0 or x > 1: return
					SongDisplayView_MouseClickCallback(x)
	except Exception:
		SongDisplayView = objc.lookUpClass("SongDisplayView") # already defined earlier

	subview = SongDisplayView.alloc().initWithFrame_(((10.0, 10.0), (80.0, 80.0)))
	subview.setTitlePosition_(AppKit.NSNoTitle)
	#subview.setContentViewMargins_((0,0))
	imgview = AppKit.NSImageView.alloc().initWithFrame_(subview.contentView().bounds())
	imgview.setImageScaling_(AppKit.NSScaleToFit)
	imgview2 = AppKit.NSImageView.alloc().initWithFrame_(((0,0), (10, subview.contentView().bounds().size.height)))
	imgview2.setImageScaling_(AppKit.NSScaleToFit)
	subview.contentView().addSubview_(imgview)
	subview.contentView().addSubview_(imgview2)
	imgview.setAutoresizingMask_(AppKit.NSViewWidthSizable|AppKit.NSViewHeightSizable)
	imgview2.setAutoresizingMask_(AppKit.NSViewHeightSizable|AppKit.NSViewMinXMargin|AppKit.NSViewMaxXMargin)

	from threading import Lock
	from State import state

	class SongDisplay:
		def __init__(self):
			self.lock = Lock()
			self.curSong = None

		def initSongCursorImg(self):
			img2 = AppKit.NSImage.alloc().initWithSize_((5,1))
			img2.lockFocus()
			for i in range(5):
				a = 100 - abs(i - 2) * 50
				AppKit.NSColor.colorWithDeviceRed_green_blue_alpha_(0.0,0.0,0.0,a).setFill()
				AppKit.NSBezierPath.fillRect_(((i,0),(1,1)))
			img2.unlockFocus()
			do_in_mainthread(lambda: imgview2.setImage_(img2))

		def setSongBitmap(self, bmpData, wait=True):
			with self.lock:
				if state.player.curSong is not self.curSong: return None
			data = AppKit.NSData.alloc().initWithBytes_length_(bmpData, len(bmpData))
			img = AppKit.NSImage.alloc().initWithData_(data)
			do_in_mainthread(lambda: imgview.setImage_(img), wait=wait)

		def getBmpData(self):
			better_exchook.install()
			pool = AppKit.NSAutoreleasePool.alloc().init() # for setSongBitmap

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

					song._useDb = False
					song.openFile()
					import ffmpeg
					bmpThumbRet = ffmpeg.calcBitmapThumbnail(song, 600, 81, procCallback = calcBmpCallback)
					if bmpThumbRet:
						queue.put(bmpThumbRet)
				except:
					print "doBmpCalc raised exception"
					sys.excepthook(*sys.exc_info())
				queue.put(None)
			queue = AsyncTask(func=doBmpCalc, name="doBmpCalc for Cocoa")

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
			pool = AppKit.NSAutoreleasePool.alloc().init()

			def updateCursor():
				with self.lock:
					if self.curSong is None: return
					if state.player.curSong is not self.curSong: return
					w = imgview2.frame().size.width
					h = imgview2.frame().size.height
					x = subview.contentView().bounds().size.width * state.player.curSongPos / self.curSong.duration - w / 2
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
				control.parent.childs["curSongPos"].updateContent()

			del pool

		def update(self, ev=None, args=None, kwargs=None):
			#if ev is PlayerEventCallbacks.onSongChange:
			with self.lock:
				if self.curSong is state.player.curSong: return # song not changed
				self.curSong = state.player.curSong

			if not self.curSong:
				do_in_mainthread(lambda: imgview.setImage_(None), wait=False)
				return

			utils.daemonThreadCall(self.getBmpData, name="GUI song bitmap loader")

	songDisplay = SongDisplay()
	songDisplay.initSongCursorImg()
	utils.daemonThreadCall(songDisplay.playCursorUpdater, name="GUI play cursor updater")

	control.nativeGuiObject = subview
	control.updateContent = songDisplay.update	
	return control


@DoInMainthreadDecorator
def buildControl(userAttr, parent):
	control = CocoaGuiObject()
	control.root = parent.root
	control.parent = parent
	control.attr = userAttr
	control.subjectObject = userAttr.__get__(parent.subjectObject)
	typeName = userAttr.getTypeClass().__name__
	assert userAttr.getTypeClass() is getattr(Traits, typeName)
	buildFuncName = "buildControl" + typeName
	buildFunc = globals().get(buildFuncName, None)
	if buildFunc:
		return buildFunc(control)
	else:
		raise NotImplementedError, "%r not handled yet" % userAttr.type

try:
	windows
except NameError:
	windows = {}


def setupWindow(subjectObject, windowName, title, isMainWindow=False):
	# some example code: http://lists.apple.com/archives/cocoa-dev/2004/Jan/msg01389.html
	# also, these might be helpful:
	# https://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/ControlCell/ControlCell.html#//apple_ref/doc/uid/10000015i
	# http://cocoadev.com/wiki/FlowLayoutView

	assert AppKit.NSThread.isMainThread()

	if getWindow(windowName):
		getWindow(windowName).makeKeyAndOrderFront_(None)
		return

	win = AppKit.NSWindow.alloc()
	win.initWithContentRect_styleMask_backing_defer_(
		((200.0, 500.0), (400.0, 600.0)),
		AppKit.NSTitledWindowMask |
		AppKit.NSClosableWindowMask |
		AppKit.NSMiniaturizableWindowMask |
		AppKit.NSResizableWindowMask,
		AppKit.NSBackingStoreBuffered, False)
	win.setContentView_(NSFlippedView.alloc().init())
	win.contentView().setAutoresizingMask_(AppKit.NSViewWidthSizable|AppKit.NSViewHeightSizable)
	
	win.setTitle_(title)

	window = CocoaGuiObject()
	window.root = window
	window.subjectObject = subjectObject
	window.nativeGuiObject = win.contentView()
	assert window.root.nativeGuiObject.window() is not None
	w,h = window.setupChilds()

	win.setContentMinSize_((w,h))
	
	win.setFrameUsingName_(windowName)
	win.setFrameAutosaveName_(windowName)
	win.display()
	win.orderFrontRegardless()
	win.makeMainWindow()
	win.makeKeyWindow()
	
	AppKit.NSApp.activateIgnoringOtherApps_(True)
	# see http://stackoverflow.com/questions/12292151/crash-in-class-getname-in-applicationopenuntitledfile
	win.retain()

	global windows
	windows[windowName] = window

def setupMainWindow():
	from State import state
	import appinfo
	setupWindow(state, windowName="mainWindow", title=appinfo.progname, isMainWindow=True)

def setupSearchWindow():
	from Search import search
	setupWindow(search, windowName="searchWindow", title="Search")

def setupSongEditWindow():
	from SongEdit import SongEdit
	import gui
	ctx = gui.ctx()
	if not getattr(ctx, "songEdit", None):
		ctx.songEdit = SongEdit(ctx)
	setupWindow(ctx.songEdit, windowName="songEditWindow", title="Song edit")	
	
def locateFile(filename):
	ws = AppKit.NSWorkspace.sharedWorkspace()
	ws.selectFile_inFileViewerRootedAtPath_(filename, None)



def guiMain():
	from player import PlayerEventCallbacks
	pool = AppKit.NSAutoreleasePool.alloc().init()
	from State import state
	for ev,args,kwargs in state.updates.read():
		try:
			# Note: This shouldn't be needed. Each GUI object should
			# get an event itself about some change.
			global windows
			for w in windows.values():
				w.updateContent()
			if ev is PlayerEventCallbacks.onPlayingStateChange or ev is PlayerEventCallbacks.onSongChange:
				updateControlMenu()
		except Exception:
			sys.excepthook(*sys.exc_info())
	del pool



if "isReload" in globals():
	isReload = True
else:
	isReload = False

if isReload:
	print "Reloading GUI not really supported..."

