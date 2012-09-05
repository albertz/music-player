
# http://weblog.rogueamoeba.com/2007/09/29/apple-keyboard-media-key-event-handling/

import AppKit
from AppKit import NSKeyUp, NSSystemDefined, NSEvent
import Quartz
import sys

class MacMediaKeyEventsTap:
	def __init__(self):
		# IOKit/hidsystem/ev_keymap.h
		self._keyControls = {
			16: 'play-pause',
			17: 'next',
			18: 'previous',
			19: 'next', # actually 'fast', but we handle it like next
			20: 'previous', # actually 'rewind', but we handle it like previous
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
					self.onMediaKeyUp(self._keyControls[keyCode])
				return None # consume event
		return event # pass through
		
	def onMediaKeyUp(self, control):
		#print "handleKeyUp:", control
		pass
		
	def runEventsCapture(self):
		pool = AppKit.NSAutoreleasePool.alloc().init()
		
		self.runLoopRef = Quartz.CFRunLoopGetCurrent()
		
		while True:
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
				self.runLoopRef,
				runLoopSource,
				Quartz.kCFRunLoopDefaultMode
			)

			# Enable the tap
			Quartz.CGEventTapEnable(tap, True)

			try:
				# and run! This won't return until we exit or are terminated.
				Quartz.CFRunLoopRun()
			except:
				# I got this one here once:
				# error: NSInternalInconsistencyException - Invalid parameter not satisfying: cgsEvent.type > 0 && cgsEvent.type <= kCGSLastEventType
				sys.excepthook(*sys.exc_info())
				continue # rerun

			# this is a regular quit
			break

		del pool
        
	def start(self):
		from threading import Thread
		self.thread = Thread(target = self.runEventsCapture)
		self.thread.start()

	def stop(self):
		Quartz.CFRunLoopStop(self.runLoopRef)


EventListener = MacMediaKeyEventsTap

from State import state

def onMediaKeyUp(control):
	try:
		if control == "play-pause":
			state.player.playing = not state.player.playing
		elif control == "next":
			state.player.nextSong()
	except:
		sys.excepthook(*sys.exc_info())

def mediakeysMain():
	eventTap = EventListener()
	eventTap.onMediaKeyUp = onMediaKeyUp
	eventTap.start()
	for ev in state.updates.read(): pass # wait for exit
	eventTap.stop()


if __name__ == '__main__':
	tap = EventListener()
	def onMediaKeyUp(control):
		print "onMediaKeyUp:", control
	tap.onMediaKeyUp = onMediaKeyUp
	tap.start()

	import time, sys
	try:
		while True: time.sleep(10)
	except: pass
	tap.stop()
	print
