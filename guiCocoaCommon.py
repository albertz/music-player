
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
		onMouseUp = None
		onDraggingEntered = None
		onDraggingUpdated = None
		onDraggingExited = None
		onPerformDragOperation = None
		_drawsBackground = False
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
		def isOpaque(self): return self._drawsBackground
		def drawRect_(self, dirtyRect):
			if self._drawsBackground:
				self._backgroundColor.setFill()
				NSRectFill(dirtyRect)
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



# keep old pools. there is no real safe way to know whether we still have some refs to objects
