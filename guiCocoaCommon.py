
import objc
from AppKit import *

from collections import deque
try: pools
except NameError: pools = deque()

# just in case that we are not the main thread
pools.append(NSAutoreleasePool.alloc().init())


try:
	class NSFlippedView(NSView):
		def isFlipped(self): return True
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
