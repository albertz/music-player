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
	
	AppKit.NSApp.delegate().dockMenu = m
	AppKit.NSApp.setDockMenu_(m)

	# new supermenu
	mi = mainMenu.addItemWithTitle_action_keyEquivalent_("Debug", None, "")
	m = AppKit.NSMenu.alloc().initWithTitle_("Debug")
	mainMenu.setSubmenu_forItem_(m, mi)

	m.addItemWithTitle_action_keyEquivalent_('reset player', 'resetPlayer:', '')

	AppKit.NSApp.setMainMenu_(mainMenu)

def updateControlMenu():
	if not AppKit.NSApp: return
	menu = getattr(AppKit.NSApp.delegate(), "dockMenu", None)
	if not menu: return
	from State import state
	if not state: return
	songEntry = menu.itemAtIndex_(0)
	playPauseEntry = menu.itemAtIndex_(1)
	songEntry.setTitle_(convertToUnicode(state.curSong.userString))
	if state.player.playing:
		playPauseEntry.setTitle_("Pause")
	else:
		playPauseEntry.setTitle_("Play")		

def setupAfterAppFinishedLaunching():
	import main
	main.successStartup = True

	from State import modules
	for m in modules: m.start()

	setupAppleMenu()
	setupMainWindow()
	AppKit.NSApp.updateWindows()
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


class PyAppDelegate(AppKit.NSObject):
	__metaclass__ = ObjCClassAutorenamer

	# Doc for AppDelegate protocol:
	# https://developer.apple.com/library/mac/#documentation/Cocoa/Reference/NSApplicationDelegate_Protocol/Reference/Reference.html

	def applicationShouldTerminate_(self, app):
		print "AppDelegate quit"
		return AppKit.NSTerminateNow

	def applicationOpenUntitledFile_(self, app):
		if not getWindow("mainWindow"):
			setupMainWindow()
		else:
			app.activateIgnoringOtherApps_(True)
		return True

	def userNotificationCenter_shouldPresentNotification_(self, notifCenter, notif):
		return True

	def openMainWindow_(self, app):
		setupMainWindow()
	
	def openSearchWindow_(self, app):
		setupSearchWindow()
	
	def openSongEditWindow_(self, app):
		setupSongEditWindow()

	def about_(self, app):
		import gui
		gui.about()

	def playPause_(self, app):
		from State import state
		state.playPause()
	
	def nextSong_(self, app):
		from State import state
		state.nextSong()

	def resetPlayer_(self, app):
		from State import state
		state.player.resetPlaying()


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
	def update(ev=None, args=None, kwargs=None):
		do_in_mainthread(do_update, wait=False)
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
	

def buildControlOneLineText(control):
	label = NSExtendedTextField.alloc().initWithFrame_(((0, 0), (30.0, 22.0)))
	label.setBordered_(False)
	if control.attr.withBorder:
		label.setBezeled_(True)
		label.setBezelStyle_(AppKit.NSTextFieldRoundedBezel)
	label.setDrawsBackground_(False)
	label.setEditable_(False)
	label.cell().setUsesSingleLineMode_(True)
	label.cell().setLineBreakMode_(AppKit.NSLineBreakByTruncatingTail)
	control.nativeGuiObject = label
	control.getTextObj = lambda: control.subjectObject
	def getTextColor():
		if any([(c.attr and c.attr.lowlight) for c in control.allParents()]):
			return AppKit.NSColor.disabledControlTextColor()
		return AppKit.NSColor.blackColor()
	control.getTextColor = getTextColor
	
	def update(ev=None, args=None, kwargs=None):
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		s = "???"
		try:
			labelContent = control.getTextObj()
			s = convertToUnicode(labelContent)
		except Exception:
			sys.excepthook(*sys.exc_info())
		def do_update():
			label.setStringValue_(s)
			
			if backgroundColor(control):
				label.setDrawsBackground_(True)
				label.setBackgroundColor_(backgroundColor(control))
			label.setTextColor_(foregroundColor(control))
			
			if control.attr.autosizeWidth:
				label.sizeToFit()
				control.layoutLine()
			
			if label.onMouseEntered or label.onMouseExited:
				if getattr(label, "trackingRect", None):
					label.removeTrackingRect_(label.trackingRect)	
				label.trackingRect = label.addTrackingRect_owner_userData_assumeInside_(label.bounds(), label, None, False)

		do_in_mainthread(do_update, wait=False)

	control.updateContent = update
	return control

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
		control.parent.updateContent(None,None,None)
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
	
	def update(ev=None, args=None, kwargs=None):
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

def buildControlList(control):
	list = control.subjectObject
	scrollview = AppKit.NSScrollView.alloc().initWithFrame_(((0.0, 0.0), (80.0, 80.0)))
	scrollview.setAutoresizingMask_(AppKit.NSViewWidthSizable|AppKit.NSViewHeightSizable)
	scrollview.contentView().setAutoresizingMask_(AppKit.NSViewWidthSizable|AppKit.NSViewHeightSizable)
	scrollview.setDocumentView_(NSFlippedView.alloc().initWithFrame_(((0,0),scrollview.contentSize())))
	scrollview.documentView().setAutoresizingMask_(AppKit.NSViewWidthSizable)
	scrollview.setHasVerticalScroller_(True)
	scrollview.setDrawsBackground_(False)
	scrollview.setBorderType_(AppKit.NSBezelBorder)
	#scrollview.setBorderType_(NSGrooveBorder)
	view = NSFlippedView.alloc().initWithFrame_(scrollview.frame())
	view.setAutoresizingMask_(AppKit.NSViewWidthSizable|AppKit.NSViewHeightSizable)
	view.addSubview_(scrollview)
	view.control = ref(control)
	
	control.nativeGuiObject = view
	control.guiObjectList = [] # all access on this list is done in the main thread
	control.OuterSpace = (0,0)
	# Hm, why did i needed this again? This makes everything slow and because of
	# the generic GuiControl.layout(), it also makes it wrong.
	#control.childIter = lambda: control.guiObjectList
	#control.childGuiObjectsInColumn = lambda: control.guiObjectList

	class Updater:
		def __init__(self):
			from threading import Lock
			self.lock = Lock()
			self.outstandingUpdate = False
		
		def doUpdate(self):
			with self.lock:
				if not self.outstandingUpdate: return
				
			x,y = 0,0
			for subCtr in control.guiObjectList:
				w = scrollview.contentSize().width
				h = subCtr.size[1]
				subCtr.pos = (x,y)
				subCtr.size = (w,h)
				y += subCtr.size[1]
			scrollview.documentView().setFrameSize_((scrollview.contentSize().width, y))
			
			if control.attr.autoScrolldown:
				scrollview.verticalScroller().setFloatValue_(1)
				scrollview.contentView().scrollToPoint_(
					(0, scrollview.documentView().frame().size.height -
						scrollview.contentSize().height))

			with self.lock:
				self.outstandingUpdate = False

		def update(self):			
			with self.lock:
				if self.outstandingUpdate: return
				self.outstandingUpdate = True
				do_in_mainthread(self.doUpdate, wait=False)
	
	updater = Updater()
	
	class AttrWrapper(UserAttrib):
		def __init__(self, index, value, parent):
			UserAttrib.__init__(self)
			self.index = index
			self.value = value
		def __get__(self, inst):
			return self.value
	def buildControlForIndex(index, value):
		subCtr = CocoaGuiObject()
		subCtr.subjectObject = value
		subCtr.root = control.root
		subCtr.parent = control
		subCtr.attr = AttrWrapper(index, value, control)
		presetSize = (scrollview.contentSize().width, 80)
		if len(control.guiObjectList) > 0:
			presetSize = (presetSize[0], control.guiObjectList[0].size[1])
		subCtr.presetSize = presetSize
		_buildControlObject_pre(subCtr)
		
		subCtr.autoresize = (False,False,True,False)
		subCtr.pos = (0,-subCtr.size[1]) # so that there isn't any flickering
		subCtr.nativeGuiObject.setDrawsBackground_(True)

		def delayedBuild():
			if control.root.nativeGuiObject.window() is None: return # window was closed
			if getattr(subCtr, "obsolete", False): return # can happen in the meanwhile
			
			w,h = subCtr.setupChilds()			
			def setSize():
				w = scrollview.contentSize().width
				subCtr.size = (w, h)
			do_in_mainthread(setSize, wait=False)
			do_in_mainthread(lambda: _buildControlObject_post(subCtr), wait=False)
			do_in_mainthread(lambda: subCtr.updateContent(None,None,None), wait=False)
			def addView():
				if getattr(subCtr, "obsolete", False): return # can happen in the meanwhile
				scrollview.documentView().addSubview_(subCtr.nativeGuiObject)
				if h != presetSize[1]:
					updater.update()
			do_in_mainthread(addView, wait=False)
	
		utils.daemonThreadCall(
			delayedBuild, name="GUI list item delayed build",
			queue="GUI-list-item-delayed-build-%i" % (index % 5)
			)
		
		return subCtr
	
	control.select = None
	if control.attr.canHaveFocus:
		class SelectionHandling:
			# for now, a single index. later maybe a range
			index = None
			def onInsert(self, index, value):
				if index <= self.index: self.index += 1
			def onRemove(self, index):
				if index < self.index: self.index -= 1
				elif index == self.index: self.deselect()
			def onClear(self):
				self.index = None
			@ExceptionCatcherDecorator
			def deselect(self):
				if self.index is not None:
					control.guiObjectList[self.index].nativeGuiObject.setBackgroundColor_(AppKit.NSColor.textBackgroundColor())
					self.index = None
			@ExceptionCatcherDecorator
			def select(self, index=None):
				self.deselect()
				if index is None:
					if len(control.guiObjectList) == 0: return
					index = 0
				self.index = index
				guiObj = control.guiObjectList[index].nativeGuiObject
				guiObj.setBackgroundColor_(AppKit.NSColor.selectedTextBackgroundColor())
				
				# special handling for gui.ctx().curSelectedSong
				if control.guiObjectList[index].subjectObject.__class__.__name__ == "Song":
					import gui
					gui.ctx().curSelectedSong = control.guiObjectList[index].subjectObject
				
				def doScrollUpdate():
					if not guiObj.window(): return # window closed or removed from window in the meantime
					objFrame = guiObj.frame()
					visibleFrame = scrollview.contentView().documentVisibleRect()
					if objFrame.origin.y < visibleFrame.origin.y:				
						scrollview.contentView().scrollToPoint_((0, objFrame.origin.y))
					elif objFrame.origin.y + objFrame.size.height > visibleFrame.origin.y + visibleFrame.size.height:
						scrollview.contentView().scrollToPoint_((0, objFrame.origin.y + objFrame.size.height - scrollview.contentSize().height))
					scrollview.reflectScrolledClipView_(scrollview.contentView())
				do_in_mainthread(doScrollUpdate, wait=False)
			def onFocus(self):
				if self.index is None:
					self.select()
				view.setDrawsFocusRing_(True)
			def onLostFocus(self):
				view.setDrawsFocusRing_(False)
			@ExceptionCatcherDecorator
			def onKeyDown(self, ev):
				# see HIToolbox/Events.h for keycodes
				if ev.keyCode() == 125: # down
					if self.index is None:
						self.select()
					elif self.index < len(control.guiObjectList) - 1:
						self.select(self.index + 1)
					return True
				elif ev.keyCode() == 126: # up
					if self.index is None:
						self.select()
					elif self.index > 0:
						self.select(self.index - 1)
					return True
				elif ev.keyCode() == 0x33: # delete
					if self.index is not None:
						index = self.index
						if self.index > 0:
							self.select(self.index - 1)
						list.remove(index)
						return True
				elif ev.keyCode() == 0x75: # forward delete
					if self.index is not None:
						index = self.index
						if self.index < len(control.guiObjectList) - 1:
							self.select(self.index + 1)
						list.remove(index)
						return True
			@ExceptionCatcherDecorator
			def onMouseDown(self, ev):
				view.window().makeFirstResponder_(view)
				mouseLoc = scrollview.documentView().convertPoint_toView_(ev.locationInWindow(), None)
				for index,obj in enumerate(control.guiObjectList):
					if AppKit.NSPointInRect(mouseLoc, obj.nativeGuiObject.frame()):
						self.select(index)
						return True
			@ExceptionCatcherDecorator
			def onInternalDrag(self, sourceControl, index, filenames):
				if sourceControl.parent is control: # internal drag to myself
					oldIndex = self.index
					# check if the index is still correct
					if control.guiObjectList[oldIndex] is sourceControl:
						self.select(index)
						list.remove(oldIndex)
				
		control.select = SelectionHandling()
		view.onBecomeFirstResponder = control.select.onFocus
		view.onResignFirstResponder = control.select.onLostFocus
		view.onKeyDown = control.select.onKeyDown
		view.onMouseDown = control.select.onMouseDown
	
	control.dragHandler = None
	if control.attr.dragHandler:
		view.registerForDraggedTypes_([AppKit.NSFilenamesPboardType])
		class DragHandler:
			index = None
			def __init__(self):
				view = NSFlippedView.alloc().initWithFrame_(((0,0),(scrollview.contentSize().width,2)))
				view.setAutoresizingMask_(AppKit.NSViewWidthSizable)
				view.setBackgroundColor_(AppKit.NSColor.blackColor())
				self.guiCursor = view
				scrollview.documentView().addSubview_(view)
			@ExceptionCatcherDecorator
			def onDraggingUpdated(self, sender):
				self.guiCursor.setDrawsBackground_(True)
				scrollview.documentView().addSubview_positioned_relativeTo_(self.guiCursor, AppKit.NSWindowAbove, None)
				dragLoc = scrollview.documentView().convertPoint_toView_(sender.draggingLocation(), None)
				self.index = 0
				y = 0
				for index,obj in enumerate(control.guiObjectList):
					frame = obj.nativeGuiObject.frame()
					if dragLoc.y > frame.origin.y + frame.size.height / 2:
						self.index = index + 1
						y = frame.origin.y + frame.size.height
					else:
						break
				self.guiCursor.setFrameOrigin_((0,y - 1))

				visibleFrame = scrollview.contentView().documentVisibleRect()
				mouseLoc = AppKit.NSPoint(dragLoc.x - visibleFrame.origin.x, dragLoc.y - visibleFrame.origin.y)
				ScrollLimit = 30
				Limit = 15
				y = None
				if mouseLoc.y < Limit:
					scrollBy = Limit - mouseLoc.y
					y = visibleFrame.origin.y - scrollBy
					y = max(y, -ScrollLimit)
				elif mouseLoc.y > visibleFrame.size.height - Limit:
					scrollBy = mouseLoc.y - visibleFrame.size.height + Limit
					y = visibleFrame.origin.y + scrollBy
					y = min(y, scrollview.documentView().frame().size.height - visibleFrame.size.height + ScrollLimit)
				if y is not None:
					scrollview.contentView().scrollToPoint_((0, y))
					scrollview.reflectScrolledClipView_(scrollview.contentView())

			def onDraggingExited(self, sender):
				self.guiCursor.setDrawsBackground_(False)
				self.index = None
			@ExceptionCatcherDecorator
			def onPerformDragOperation(self, sender):
				self.guiCursor.setDrawsBackground_(False)
				import __builtin__
				try:
					filenames = __builtin__.list(sender.draggingPasteboard().propertyListForType_(AppKit.NSFilenamesPboardType))
					filenames = map(convertToUnicode, filenames)
					index = self.index
					internalDragCallback = getattr(sender.draggingSource(), "onInternalDrag", None)
					def doDragHandler():
						control.attr.dragHandler(
							control.parent.subjectObject,
							control.subjectObject,
							index,
							filenames)
						if internalDragCallback:
							do_in_mainthread(lambda:
								internalDragCallback(
									control,
									index,
									filenames),
								wait=False)
					utils.daemonThreadCall(doDragHandler, name="DragHandler")
					return True
				except:
					sys.excepthook(*sys.exc_info())
					return False
			@ExceptionCatcherDecorator
			def onInternalDrag(self, *args):
				# Note: This doesn't work if we don't have attr.canHaveFocus. Should be fixed later...
				control.select.onInternalDrag(*args)
				
		control.dragHandler = DragHandler()
		view.onDraggingUpdated = control.dragHandler.onDraggingUpdated
		view.onDraggingExited = control.dragHandler.onDraggingExited
		view.onPerformDragOperation = control.dragHandler.onPerformDragOperation	
	
	def doInitialFill():
		with list.lock:
			import __builtin__
			listCopy = __builtin__.list(list)
			
			control.guiObjectList = []
			Step = 5
			def doInitialAddSome(iStart):
				for i in range(iStart, min(len(listCopy), iStart+Step)):
					control.guiObjectList += [buildControlForIndex(i, listCopy[i])]
				updater.update()
				
			for i in xrange(0, len(listCopy), Step):
				do_in_mainthread(lambda: doInitialAddSome(i), wait=True)
			
			def list_onInsert(index, value):
				control.guiObjectList.insert(index, buildControlForIndex(index, value))
				updater.update()
			def list_onRemove(index):
				control.guiObjectList[index].obsolete = True
				control.guiObjectList[index].nativeGuiObject.removeFromSuperview()
				del control.guiObjectList[index]
				updater.update()
			def list_onClear():
				for subCtr in control.guiObjectList:
					subCtr.nativeGuiObject.removeFromSuperview()
					subCtr.obsolete = True
				del control.guiObjectList[:]
				updater.update()
			
			for ev in ["onInsert","onRemove","onClear"]:
				f = locals()["list_" + ev]
				def wrap(f=f, ev=ev):
					def handler(*args):
						if control.select: getattr(control.select, ev)(*args)
						f(*args)
					return lambda *args: do_in_mainthread(lambda: handler(*args), wait=False)
				setattr(list, ev, wrap())
	utils.daemonThreadCall(doInitialFill, name="List initial fill")
	
	return control

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

	def update(ev=None, args=None, kwargs=None):
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

	def update(ev=None, args=None, kwargs=None):
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		value = control.subjectObject
		do_in_mainthread(lambda: slider.setDoubleValue_(value), wait=False)
	control.updateContent = update

	def onValueChange(newValue):
		control.attr.__set__(control.parent.subjectObject, newValue)	
	slider.onValueChange = onValueChange
	return control

def buildControlObject(control):
	_buildControlObject_pre(control)
	w,h = control.setupChilds()
	control.size = (w,h)
	_buildControlObject_post(control)
	return control

def _buildControlObject_pre(control):
	presetSize = getattr(control, "presetSize", (80.0,80.0))	
	subview = NSFlippedView.alloc().initWithFrame_(((10.0, 10.0), presetSize))
	subview.control = ref(control)
	control.nativeGuiObject = subview
	control.OuterSpace = (0,0)
	
def _buildControlObject_post(control):
	subview = control.nativeGuiObject

	if control.attr.canHaveFocus:
		subview.setDrawsBackground_(True)
		subview.onResignFirstResponder = lambda: subview.setBackgroundColor_(AppKit.NSColor.textBackgroundColor())
		subview.onBecomeFirstResponder = lambda: subview.setBackgroundColor_(AppKit.NSColor.selectedTextBackgroundColor())
		
	if backgroundColor(control):
		subview.setDrawsBackground_(True)
		subview.setBackgroundColor_(backgroundColor(control))
	
	@ExceptionCatcherDecorator
	def onInternalDrag(target, listindex, filenames):
		attrChain(target, "dragHandler", "onInternalDrag")(control, listindex, filenames)
	
	@ExceptionCatcherDecorator
	def onMouseDragged(ev):
		guiObj = control
		subjectObj = guiObj.subjectObject
		filename = getattr(subjectObj, "url", None)
		if not filename: return False
		filename = convertToUnicode(filename)
		pboard = AppKit.NSPasteboard.pasteboardWithName_(AppKit.NSDragPboard)
		pboard.declareTypes_owner_([AppKit.NSFilenamesPboardType], None)
		pboard.setPropertyList_forType_([filename], AppKit.NSFilenamesPboardType)
		dragImage = AppKit.NSWorkspace.sharedWorkspace().iconForFile_(filename)
		dragPosition = subview.convertPoint_toView_(ev.locationInWindow(), None)
		dragPosition.x -= 16
		dragPosition.y += 32
		dragSource = DragSource.alloc().init()
		dragSource.onInternalDrag = onInternalDrag
		subview.dragImage_at_offset_event_pasteboard_source_slideBack_(
			dragImage,
			dragPosition,
			AppKit.NSZeroSize,
			ev,
			pboard,
			dragSource,
			False
		)
		return True		
	subview.onMouseDragged = onMouseDragged
	
	@ExceptionCatcherDecorator
	def onMouseDown(ev):
		subjectObj = control.subjectObject
		# special handling for gui.ctx().curSelectedSong
		if subjectObj.__class__.__name__ == "Song":
			import gui
			gui.ctx().curSelectedSong = subjectObj	
	subview.onMouseDown = onMouseDown
	

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
				control.parent.childs["curSongPos"].updateContent(None,None,None)

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

class CocoaGuiObject(object):
	def __init__(self):
		# Do that late because we cannot import gui globally here. (circular dep)
		import gui
		self.__class__.__bases__ = (gui.GuiObject, object)
	
	nativeGuiObject = None
	
	@property
	@DoInMainthreadDecorator
	def pos(self): return (self.nativeGuiObject.frame().origin.x, self.nativeGuiObject.frame().origin.y)	
	@pos.setter
	@DoInMainthreadDecorator
	def pos(self, value): self.nativeGuiObject.setFrameOrigin_(value)
	@property
	@DoInMainthreadDecorator
	def size(self): return (self.nativeGuiObject.frame().size.width, self.nativeGuiObject.frame().size.height)
	@size.setter
	@DoInMainthreadDecorator
	def size(self, value): self.nativeGuiObject.setFrameSize_(value)
	@property
	@DoInMainthreadDecorator
	def innerSize(self): return (self.nativeGuiObject.bounds().size.width, self.nativeGuiObject.bounds().size.height)

	@property
	@DoInMainthreadDecorator
	def autoresize(self):
		flags = self.nativeGuiObject.autoresizingMask()
		return (flags & AppKit.NSViewMinXMargin, flags & AppKit.NSViewMinYMargin, flags & AppKit.NSViewWidthSizable, flags & AppKit.NSViewHeightSizable)
	@autoresize.setter
	@DoInMainthreadDecorator
	def autoresize(self, value):
		flags = 0
		if value[0]: flags |= AppKit.NSViewMinXMargin
		if value[1]: flags |= AppKit.NSViewMinYMargin
		if value[2]: flags |= AppKit.NSViewWidthSizable
		if value[3]: flags |= AppKit.NSViewHeightSizable
		self.nativeGuiObject.setAutoresizingMask_(flags)
		
	@DoInMainthreadDecorator
	def addChild(self, child):
		self.nativeGuiObject.addSubview_(child.nativeGuiObject)
		
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
				w.updateContent(ev,args,kwargs)
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

