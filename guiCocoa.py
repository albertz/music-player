
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
	
	m.addItemWithTitle_action_keyEquivalent_('About MusicPlayer', 'about:', '')
	m.addItemWithTitle_action_keyEquivalent_('Main window', 'openMainWindow:', '')
	m.addItemWithTitle_action_keyEquivalent_('Search window', 'openSearchWindow:', '')
	m.addItemWithTitle_action_keyEquivalent_('Minimize window', 'miniaturize:', 'm')
	m.addItemWithTitle_action_keyEquivalent_('Close window', 'performClose:', 'w')
	m.addItemWithTitle_action_keyEquivalent_('Quit', 'terminate:', 'q')

	app.setMainMenu_(mainMenu)

	return m

def setupAfterAppFinishedLaunching(delegate):
	setupAppleMenu()
	setupMainWindow()
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
		# first set/send signals to all modules
		for m in modules: m.stop(join=False)
		try:
			# in case there are any subprocesses, interrupt them
			# maybe some modules are hanging and waiting for such
			import sys, os, signal
			os.kill(0, signal.SIGINT)
		except: pass
		# now join all
		for m in modules: m.stop()
		return NSTerminateNow

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
	
	def about_(self, app):
		import webbrowser
		webbrowser.open("http://albertz.github.com/music-player/")
		
def getWindow(name):
	global windows
	if windows.get(name, None):
		return windows[name].nativeGuiObject.window()
	return None

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
	control.buttonActionHandler = actionTarget # keep ref here. button.target() is only a weakref
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


def backgroundColor(control):
	if any([(c.attr and c.attr.highlight) for c in control.allParents()]):
		return NSColor.blueColor()
	return None

def foregroundColor(control):
	if any([(c.attr and c.attr.lowlight) for c in control.allParents()]):
		return NSColor.disabledControlTextColor()
	return NSColor.blackColor()		
	

def buildControlOneLineText(control):
	label = NSExtendedTextField.alloc().initWithFrame_(((0, 0), (30.0, 22.0)))
	label.setBordered_(False)
	if control.attr.withBorder:
		label.setBezeled_(True)
		label.setBezelStyle_(NSTextFieldRoundedBezel)
	label.setDrawsBackground_(False)
	label.setEditable_(False)
	label.cell().setUsesSingleLineMode_(True)
	label.cell().setLineBreakMode_(NSLineBreakByTruncatingTail)
	control.nativeGuiObject = label
	control.getTextObj = lambda: control.subjectObject
	def getTextColor():
		if any([(c.attr and c.attr.lowlight) for c in control.allParents()]):
			return NSColor.disabledControlTextColor()
		return NSColor.blackColor()		
	control.getTextColor = getTextColor
	
	def update(ev, args, kwargs):
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		labelContent = control.getTextObj()
		s = "???"
		try:
			s = convertToUnicode(labelContent)
		except: pass
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
		if label.backgroundColor() == NSColor.blueColor():
			label.setTextColor_(NSColor.grayColor())			
		else:
			label.setTextColor_(NSColor.blueColor())
	label.onMouseEntered = onMouseEntered
	label.onMouseExited = lambda ev: label.setTextColor_(foregroundColor(control))
	label.onMouseDown = lambda ev: (
		control.subjectObject(handleClick=True),
		control.parent.updateContent(None,None,None)
		)

	return control

def buildControlEditableText(control):
	label = NSExtendedTextField.alloc().initWithFrame_(((0, 0), (30.0, 22.0)))
	if control.attr.searchLook:
		label.setCell_(NSSearchFieldCell.alloc().init())
	label.setBordered_(False)
	label.setBezeled_(True)
	label.setBezelStyle_(NSTextFieldRoundedBezel)
	label.setDrawsBackground_(True)
	label.setEditable_(True)
	label.cell().setUsesSingleLineMode_(True)
	#label.cell().setLineBreakMode_(NSLineBreakByTruncatingTail)
	control.nativeGuiObject = label
	control.getTextObj = lambda: control.subjectObject()
	
	def update(ev, args, kwargs):
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		labelContent = control.getTextObj()
		s = "???"
		try:
			s = convertToUnicode(labelContent)
		except: pass
		def do_update():
			label.setStringValue_(s)

		do_in_mainthread(do_update, wait=False)

	control.updateContent = update

	def onTextChange():
		try:
			control.subjectObject = control.attr.__get__(control.parent.subjectObject)
			newText = unicode(label.stringValue())
			control.subjectObject(updateText = newText)
		except:
			sys.excepthook(*sys.exc_info())
			
	label.onTextChange = onTextChange

	return control

def buildControlList(control):
	list = control.subjectObject
	scrollview = NSScrollView.alloc().initWithFrame_(((0.0, 0.0), (80.0, 80.0)))
	scrollview.setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	scrollview.contentView().setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	scrollview.setDocumentView_(NSFlippedView.alloc().initWithFrame_(((0,0),scrollview.contentSize())))
	scrollview.documentView().setAutoresizingMask_(NSViewWidthSizable)
	scrollview.setHasVerticalScroller_(True)
	scrollview.setDrawsBackground_(False)
	scrollview.setBorderType_(NSBezelBorder)
	#scrollview.setBorderType_(NSGrooveBorder)
	view = NSFlippedView.alloc().initWithFrame_(scrollview.frame())
	view.setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	view.addSubview_(scrollview)
	view.control = control
	
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
		subCtr.parent = control
		subCtr.attr = AttrWrapper(index, value, control)
		buildControlObject(subCtr)
		scrollview.documentView().addSubview_(subCtr.nativeGuiObject)
		subCtr.updateContent(None,None,None)
		subCtr.autoresize = (False,False,True,False)
		subCtr.size = (0,subCtr.size[1]) # so that there isn't any flickering
		subCtr.nativeGuiObject.setDrawsBackground_(True)
		
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
			def deselect(self):
				if self.index is not None:
					control.guiObjectList[self.index].nativeGuiObject.setBackgroundColor_(NSColor.textBackgroundColor())
					self.index = None
			def select(self, index=None):
				self.deselect()
				if index is None:
					if len(control.guiObjectList) == 0: return
					index = 0
				self.index = index
				guiObj = control.guiObjectList[index].nativeGuiObject
				guiObj.setBackgroundColor_(NSColor.selectedTextBackgroundColor())
				
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
				view.setDrawsFocusRing(True)
			def onLostFocus(self):
				view.setDrawsFocusRing(False)
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
			def onMouseDown(self, ev):
				view.window().makeFirstResponder_(view)
				mouseLoc = scrollview.documentView().convertPoint_toView_(ev.locationInWindow(), None)
				for index,obj in enumerate(control.guiObjectList):
					if NSPointInRect(mouseLoc, obj.nativeGuiObject.frame()):
						self.select(index)
						return True
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
		view.registerForDraggedTypes_([NSFilenamesPboardType])
		class DragHandler:
			index = None
			def __init__(self):
				view = NSFlippedView.alloc().initWithFrame_(((0,0),(scrollview.contentSize().width,2)))
				view.setAutoresizingMask_(NSViewWidthSizable)
				view.setBackgroundColor_(NSColor.blackColor())
				self.guiCursor = view
				scrollview.documentView().addSubview_(view)
			def onDraggingUpdated(self, sender):
				self.guiCursor.setDrawsBackground_(True)
				scrollview.documentView().addSubview_positioned_relativeTo_(self.guiCursor, NSWindowAbove, None)
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
				mouseLoc = NSPoint(dragLoc.x - visibleFrame.origin.x, dragLoc.y - visibleFrame.origin.y)
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
			def onPerformDragOperation(self, sender):
				self.guiCursor.setDrawsBackground_(False)
				import __builtin__
				try:
					filenames = __builtin__.list(sender.draggingPasteboard().propertyListForType_(NSFilenamesPboardType))
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
					from threading import Thread
					t = Thread(target=doDragHandler, name="DragHandler")
					t.daemon = True
					t.start()
					return True
				except:
					sys.excepthook(*sys.exc_info())
					return False
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
				control.guiObjectList[index].nativeGuiObject.removeFromSuperview()
				del control.guiObjectList[index]
				updater.update()
			def list_onClear():
				for subCtr in control.guiObjectList:
					subCtr.nativeGuiObject.removeFromSuperview()
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
	from threading import Thread
	t = Thread(target=doInitialFill, name="List initial fill")
	t.daemon = True
	t.start()	
	
	return control

def buildControlTable(control):
	scrollview = NSScrollView.alloc().initWithFrame_(((0.0, 0.0), (80.0, 80.0)))
	scrollview.setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	scrollview.contentView().setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	scrollview.setHasVerticalScroller_(True)
	scrollview.setDrawsBackground_(False)
	scrollview.setBorderType_(NSBezelBorder)
	
	view = NSFlippedView.alloc().initWithFrame_(scrollview.frame())
	view.setAutoresizingMask_(NSViewWidthSizable|NSViewHeightSizable)
	view.addSubview_(scrollview)
	view.control = control
	control.nativeGuiObject = view

	table = NSTableView.alloc().initWithFrame_(((0,0),(80,80)))
	scrollview.setDocumentView_(table)
	scrollview.documentView().setAutoresizingMask_(NSViewWidthSizable)
	
	#array = NSArrayController.alloc().init()
	dataSource = TableViewDataSource.alloc().init()
	dataSource.data = []
	dataSource.formaters = control.attr.type.formaters
	control.tableDataSource = dataSource # save ref here because table.dataSource() is only a weakref
	table.setDataSource_(dataSource)
	
	table.setColumnAutoresizingStyle_(NSTableViewUniformColumnAutoresizingStyle)
	for key in control.attr.type.keys:
		column = NSTableColumn.alloc().initWithIdentifier_(key)
		column.headerCell().setStringValue_(convertToUnicode(key.capitalize())) # title
		column.setEditable_(False)
		column.setMinWidth_(30)
		column.setSortDescriptorPrototype_(NSSortDescriptor.sortDescriptorWithKey_ascending_(key, True))
		table.addTableColumn_(column)
	
	table.setAllowsMultipleSelection_(True)	
	table.setAutosaveName_(control.name)
	table.setAutosaveTableColumns_(True)

	def update():
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		value = control.subjectObject
		dataSource.data = value
		table.reloadData()
	control.updateContent = lambda ev, args, kwargs: update

	if control.attr.hasUpdateEvent():
		control.attr.updateEvent(control.parent.subjectObject).register(update)

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

	def update(ev, args, kwargs):
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		value = control.subjectObject
		do_in_mainthread(lambda: slider.setDoubleValue_(value), wait=False)
	control.updateContent = update

	def onValueChange(newValue):
		control.attr.__set__(control.parent.subjectObject, newValue)	
	slider.onValueChange = onValueChange
	return control

def buildControlObject(control):
	subview = NSFlippedView.alloc().initWithFrame_(((10.0, 10.0), (80.0, 80.0)))
	subview.control = control
	control.nativeGuiObject = subview
	control.OuterSpace = (0,0)
	w,h = control.setupChilds()
	control.size = (w,h)

	if control.attr.canHaveFocus:
		subview.setDrawsBackground_(True)
		subview.onResignFirstResponder = lambda: subview.setBackgroundColor_(NSColor.textBackgroundColor())		
		subview.onBecomeFirstResponder = lambda: subview.setBackgroundColor_(NSColor.selectedTextBackgroundColor())
		
	if backgroundColor(control):
		subview.setDrawsBackground_(True)
		subview.setBackgroundColor_(backgroundColor(control))
	
	def onInternalDrag(target, listindex, filenames):
		attrChain(target, "dragHandler", "onInternalDrag")(control, listindex, filenames)
	
	def onMouseDragged(ev):
		guiObj = control
		subjectObj = guiObj.subjectObject
		filename = getattr(subjectObj, "url", None)
		if not filename: return False
		filename = convertToUnicode(filename)
		pboard = NSPasteboard.pasteboardWithName_(NSDragPboard)
		pboard.declareTypes_owner_([NSFilenamesPboardType], None)
		pboard.setPropertyList_forType_([filename], NSFilenamesPboardType)
		dragImage = NSWorkspace.sharedWorkspace().iconForFile_(filename)
		dragPosition = subview.convertPoint_toView_(ev.locationInWindow(), None)
		dragPosition.x -= 16
		dragPosition.y += 32
		dragSource = DragSource.alloc().init()
		dragSource.onInternalDrag = onInternalDrag
		subview.dragImage_at_offset_event_pasteboard_source_slideBack_(
			dragImage,
			dragPosition,
			NSZeroSize,
			ev,
			pboard,
			dragSource,
			False
		)
		return True
		
	subview.onMouseDragged = onMouseDragged
	
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
			pool = NSAutoreleasePool.alloc().init()

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
		
def setupWindow(subjectObject, windowName, title, isMainWindow=False):
	# some example code: http://lists.apple.com/archives/cocoa-dev/2004/Jan/msg01389.html
	# also, these might be helpful:
	# https://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/ControlCell/ControlCell.html#//apple_ref/doc/uid/10000015i
	# http://cocoadev.com/wiki/FlowLayoutView

	assert NSThread.isMainThread()

	if getWindow(windowName):
		getWindow(windowName).makeKeyWindow()
		return

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
	
	win.setTitle_(title)

	window = CocoaGuiObject()
	window.subjectObject = subjectObject
	window.nativeGuiObject = win.contentView()
	w,h = window.setupChilds()

	win.setContentMinSize_((w,h))
	
	win.display()
	win.orderFrontRegardless()
	win.makeMainWindow()
	win.makeKeyWindow()
	
	win.setFrameUsingName_(windowName)
	win.setFrameAutosaveName_(windowName)

	app.activateIgnoringOtherApps_(True)
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
	
def locateFile(filename):
	ws = NSWorkspace.sharedWorkspace()
	ws.selectFile_inFileViewerRootedAtPath_(filename, None)




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
	global windows
	windows.clear()
	
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
			global windows
			for w in windows.values():
				w.updateContent(ev,args,kwargs)
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

