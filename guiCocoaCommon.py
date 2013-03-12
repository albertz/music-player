# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import objc
from AppKit import *
import utils

from collections import deque
try: pools
except NameError: pools = deque()

# just in case that we are not the main thread
pools.append(NSAutoreleasePool.alloc().init())

# we have some native code in a dylib.
# later, maybe most of the code here can be recoded natively.
# this is a work-in-progress.
import ctypes, os
l = ctypes.CDLL(os.path.dirname(__file__) + "/_guiCocoaCommon.dylib")

try:	
	_NSFlippedView = objc.lookUpClass("_NSFlippedView")
	class NSFlippedView(_NSFlippedView):
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
		formaters = {}
		lock = None
		def init(self):
			import threading
			self.lock = threading.RLock()
			return self
		def numberOfRowsInTableView_(self, tableView):
			try:
				with self.lock:
					return len(self.data)
			except Exception:
				import sys
				sys.excepthook(*sys.exc_info())
			return 0
		def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, rowIndex):
			try:
				with self.lock:
					if rowIndex >= len(self.data):
						# This can happen if the data has changed in the middle
						# of a tableView.redraw().
						# Note that wrapping tableView.reloadData() doesn't work
						# because that doesn't reload it internally - it just delays
						# a redraw and inside the redraw, it reloads the data.
						# So, overriding redraw with locking might work.
						# But anyway, it doesn't really matter as we should have delayed
						# a further reloadData().
						# Also, in guiCocoa, there is another further workaround
						# which probably makes this obsolete.
						return None
					key = str(tableColumn.identifier())
					v = self.data[rowIndex].get(key, None)
					if key in self.formaters: v = self.formaters[key](v)
					if isinstance(v, str): v = utils.convertToUnicode(v)
					return v
			except Exception:
				import sys
				sys.excepthook(*sys.exc_info())
			return None
		def resort(self, tableView):
			sortDescs = list(tableView.sortDescriptors())
			def itemIter(item):
				for d in sortDescs:
					value = item.get(d.key(), None)
					if isinstance(value, (str,unicode)):
						value = value.lower()
					yield value
			def key(item):
				item = tuple(itemIter(item))
				return item
			if sortDescs:
				firstAsc = sortDescs[0].ascending()
			else:
				# sort descriptors hasn't been set yet
				firstAsc = True
			with self.lock:
				self.data.sort(key=key, reverse=not firstAsc)
		def tableView_sortDescriptorsDidChange_(self, tableView, oldDescriptors):
			try:
				with self.lock:
					self.resort(tableView)
					tableView.reloadData()
			except Exception:
				import sys
				sys.excepthook(*sys.exc_info())
		def tableView_writeRowsWithIndexes_toPasteboard_(self, tableView, rowIndexes, pboard):
			possibleSources = []
			def handleRowIndex(index, stop):
				try:
					url = self.data[index].get("url", None)
					if url:
						url = utils.convertToUnicode(url)
						possibleSources.append(url)
				except Exception:
					import sys
					sys.excepthook(*sys.exc_info())						
			with self.lock:
				rowIndexes.enumerateIndexesUsingBlock_(handleRowIndex)
			if not possibleSources: return False

			pboard.declareTypes_owner_([NSFilenamesPboardType], None)
			pboard.setPropertyList_forType_(possibleSources, NSFilenamesPboardType)
			return True
			
except:
	TableViewDataSource = objc.lookUpClass("TableViewDataSource")

try:
	class TableViewDelegate(NSObject):
		onSelectionChange = None
		def tableViewSelectionDidChange_(self, notif):
			if self.onSelectionChange:
				tableView = notif.object()
				selection = []
				def handleRowIndex(index, stop):
					try:
						selection.append(tableView.dataSource().data[index])
					except Exception:
						import sys
						sys.excepthook(*sys.exc_info())						
				tableView.selectedRowIndexes().enumerateIndexesUsingBlock_(handleRowIndex)
				try:
					self.onSelectionChange(selection)
				except Exception:
					import sys
					sys.excepthook(*sys.exc_info())						
except:
	TableViewDelegate = objc.lookUpClass("TableViewDelegate")


try:
	class ButtonActionHandler(NSObject):
		def initWithArgs(self, userAttr, inst):
			self.init()
			self.userAttr = userAttr
			self.inst = inst
			return self
		def click(self, sender):
			attr = self.userAttr.__get__(self.inst)
			utils.daemonThreadCall(attr, name="%r click handler" % (self.userAttr))
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
