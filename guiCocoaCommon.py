
import objc
from AppKit import *
import utils

from collections import deque
try: pools
except NameError: pools = deque()

# just in case that we are not the main thread
pools.append(NSAutoreleasePool.alloc().init())


try:
	class NSFlippedView(NSView):
		control = None
		onBecomeFirstResponder = None
		onResignFirstResponder = None
		onKeyDown = None
		onKeyUp = None
		onMouseDown = None
		onMouseDragged = None
		onMouseUp = None
		onDraggingEntered = None
		onDraggingUpdated = None
		onDraggingExited = None
		onPerformDragOperation = None
		_drawsBackground = False
		_drawsFocusRing = False
		_backgroundColor = None
		def isFlipped(self): return True
		def setDrawsBackground_(self, value):
			self._drawsBackground = value
			if value and not self._backgroundColor:
				self._backgroundColor = NSColor.whiteColor()
			self.setNeedsDisplay_(True)
		def setBackgroundColor_(self, value):
			self._backgroundColor = value
			if self._drawsBackground:
				self.setNeedsDisplay_(True)
		def backgroundColor(self): return self._backgroundColor
		def setDrawsFocusRing(self, value):
			self._drawsFocusRing = value
			self.setNeedsDisplay_(True)
		def isOpaque(self): return self._drawsBackground
		def drawRect_(self, dirtyRect):
			self.drawFocusRingMask()
			if self._drawsBackground:
				self._backgroundColor.setFill()
				NSRectFill(dirtyRect)
			if self._drawsFocusRing:
				NSSetFocusRingStyle(NSFocusRingOnly)
				NSRectFill(self.bounds())
		def acceptsFirstResponder(self):
			return utils.attrChain(self, "control", "attr", "canHaveFocus", default=False)
		def becomeFirstResponder(self):
			if NSView.becomeFirstResponder(self):
				if self.onBecomeFirstResponder: self.onBecomeFirstResponder()
				return True
			else:
				return False
		def resignFirstResponder(self):
			if NSView.resignFirstResponder(self):
				if self.onResignFirstResponder: self.onResignFirstResponder()				
				return True
			else:
				return False
		def keyDown_(self, ev):
			if not self.onKeyDown or not self.onKeyDown(ev):
				NSView.keyDown_(self, ev)
		def keyUp_(self, ev):
			if not self.onKeyUp or not self.onKeyUp(ev):
				NSView.keyUp_(self, ev)
		def mouseDown_(self, ev):
			if not self.onMouseDown or not self.onMouseDown(ev):
				NSView.mouseDown_(self, ev)
		def mouseDragged_(self, ev):
			if not self.onMouseDragged or not self.onMouseDragged(ev):
				NSView.mouseDragged_(self, ev)
		def mouseUp_(self, ev):
			if not self.onMouseUp or not self.onMouseUp(ev):
				NSView.mouseUp_(self, ev)
		def draggingEntered_(self, sender):
			if self.onDraggingEntered: self.onDraggingEntered(sender)
			return self.draggingUpdated_(sender)
		def draggingUpdated_(self, sender):
			if self.onDraggingUpdated: self.onDraggingUpdated(sender)
			return NSDragOperationGeneric
		def draggingExited_(self, sender):
			if self.onDraggingExited: self.onDraggingExited(sender)
		def prepareForDragOperation_(self, sender):
			return True
		def performDragOperation_(self, sender):
			if self.onPerformDragOperation and self.onPerformDragOperation(sender):
				return True
			return False

except:
	NSFlippedView = objc.lookUpClass("NSFlippedView")

try:
	class NSExtendedTextField(NSTextField):
		onMouseEntered = None
		onMouseExited = None
		onMouseDown = None
		onMouseDragged = None
		onMouseUp = None
		onTextChange = None
		def mouseEntered_(self, ev):
			if self.onMouseEntered: self.onMouseEntered(ev)
			else: NSTextField.mouseEntered_(self, ev)
		def mouseExited_(self, ev):
			if self.onMouseExited: self.onMouseExited(ev)
			else: NSTextField.mouseExited_(self, ev)
		def mouseDown_(self, ev):
			if not self.onMouseDown or not self.onMouseDown(ev):
				NSView.mouseDown_(self, ev)
		def mouseDragged_(self, ev):
			if not self.onMouseDragged or not self.onMouseDragged(ev):
				NSView.mouseDragged_(self, ev)
		def mouseUp_(self, ev):
			if not self.onMouseUp or not self.onMouseUp(ev):
				NSView.mouseUp_(self, ev)
		def textDidChange_(self, notif):
			NSTextField.textDidChange_(self, notif)
			if self.onTextChange:
				self.onTextChange()

except:
	NSExtendedTextField = objc.lookUpClass("NSExtendedTextField")

try:
	class NSExtendedSlider(NSSlider):
		onValueChange = None
		def initWithFrame_(self, frame):
			NSSlider.initWithFrame_(self, frame)
			self.setTarget_(self)
			self.setAction_("valueChange")
			return self
		def valueChange(self, sender):
			if self.onValueChange:
				self.onValueChange(self.doubleValue())
except:
	NSExtendedSlider = objc.lookUpClass("NSExtendedSlider")

try:
	class TableViewDataSource(NSObject):
		data = ()
		def numberOfRowsInTableView_(self, tableView):
			return len(self.data)
		def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, rowIndex):
			v = self.data[rowIndex].get(tableColumn.identifier(), None)
			if isinstance(v, str): v = utils.convertToUnicode(v)
			return v
		def tableView_sortDescriptorsDidChange_(self, tableView, oldDescriptors):
			sortDescs = tableView.sortDescriptors()
			def itemIter(item):
				for d in sortDescs:
					value = item.get(d.key(), None)
					if isinstance(value, (str,unicode)):
						value = value.lower()
					yield value
			def key(item):
				item = tuple(itemIter(item))
				return item
			self.data.sort(key=key, reverse=not sortDescs[0].ascending())
			tableView.reloadData()
		def tableView_writeRowsWithIndexes_toPasteboard_(self, tableView, rowIndexes, pboard):
			possibleSources = []
			def handleRowIndex(index, stop):
				url = self.data[index].get("url", None)
				if url:
					url = utils.convertToUnicode(url)
					possibleSources.append(url)
			rowIndexes.enumerateIndexesUsingBlock_(handleRowIndex)
			if not possibleSources: return False

			pboard.declareTypes_owner_([NSFilenamesPboardType], None)
			pboard.setPropertyList_forType_(possibleSources, NSFilenamesPboardType)
			return True
			
except:
	TableViewDataSource = objc.lookUpClass("TableViewDataSource")



try:
	class ButtonActionHandler(NSObject):
		def initWithArgs(self, userAttr, inst):
			self.init()
			self.userAttr = userAttr
			self.inst = inst
			return self
		def click(self, sender):
			attr = self.userAttr.__get__(self.inst)
			from threading import Thread
			Thread(target=attr, name="click handler").start()
except:
	ButtonActionHandler = objc.lookUpClass("ButtonActionHandler") # already defined earlier



try:
	class DragSource(NSObject):
		onDragEnded = None
		onInternalDrag = None
		@objc.typedSelector('i@:@i')
		def draggingSession_sourceOperationMaskForDraggingContext_(self, session, context):
			return NSDragOperationAll
		@objc.typedSelector('v@:@{CGPoint=dd}i')
		def draggingSession_endedAtPoint_operation_(self, session, screenPoint, operation):
			if self.onDragEnded: self.onDragEnded(operation)
		@objc.typedSelector('v@:@{CGPoint=dd}i')
		def draggedImage_endedAt_operation_(self, img, pt, operation):
			if self.onDragEnded: self.onDragEnded(operation)
		
except:
	DragSource = objc.lookUpClass("DragSource")

# keep old pools. there is no real safe way to know whether we still have some refs to objects
