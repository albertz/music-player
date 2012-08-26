
# http://weblog.rogueamoeba.com/2007/09/29/apple-keyboard-media-key-event-handling/

import os
import signal
import AppKit
from AppKit import NSKeyUp, NSSystemDefined, NSEvent
import Quartz

class MacKeyEventsTap:
	def __init__(self):
		# IOKit/hidsystem/ev_keymap.h
		self._keyControls = {
			16: 'play-pause',
			19: 'next',
			20: 'previous',
		}

	def eventTap(self, proxy, type_, event, refcon):
		# Convert the Quartz CGEvent into something more useful
		keyEvent = NSEvent.eventWithCGEvent_(event)
		if keyEvent.subtype() is 8: # subtype 8 is media keys
			data = keyEvent.data1()
			keyCode = (data & 0xFFFF0000) >> 16
			keyState = (data & 0xFF00) >> 8
			if keyCode in self._keyControls:
				if keyState == NSKeyUp:
					self.handleKeyUp(self._keyControls[keyCode])
				return None # consume event
		return event # pass through
		
	def handleKeyUp(self, control):
		print "handleKeyUp:", control

	def runEventsCapture(self):
		pool = AppKit.NSAutoreleasePool.alloc().init()
		
		self.runLoopRef = Quartz.CFRunLoopGetCurrent()
		
		# https://developer.apple.com/library/mac/#documentation/Carbon/Reference/QuartzEventServicesRef/Reference/reference.html
		tap = Quartz.CGEventTapCreate(
			Quartz.kCGSessionEventTap, # Quartz.kCGSessionEventTap or kCGHIDEventTap
			Quartz.kCGHeadInsertEventTap, # Insert wherever, we do not filter
			Quartz.kCGEventTapOptionDefault, #Quartz.kCGEventTapOptionListenOnly,
			Quartz.CGEventMaskBit(NSSystemDefined), # NSSystemDefined for media keys
			self.eventTap,
			None
		)
		assert tap
		# Create a runloop source and add it to the current loop
		runLoopSource = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
		Quartz.CFRunLoopAddSource(
			Quartz.CFRunLoopGetCurrent(),
			runLoopSource,
			Quartz.kCFRunLoopDefaultMode
		)
		# Enable the tap
		Quartz.CGEventTapEnable(tap, True)
		# and run! This won't return until we exit or are terminated.
		from threading import Thread
		Quartz.CFRunLoopRun()

	def stop(self):
		Quartz.CFRunLoopStop(self.runLoopRef)
		
if __name__ == '__main__':
	tap = MacKeyEventsTap()
	from threading import Thread
	t = Thread(target=tap.runEventsCapture)
	t.start()
	import time, sys
	try:
		while True: time.sleep(10)
	except: pass
	tap.stop()
	print
	