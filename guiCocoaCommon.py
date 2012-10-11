
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
