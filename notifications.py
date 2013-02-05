# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

def macNotificationsMain():
	from State import state
	from player import PlayerEventCallbacks
	import AppKit
	import utils

	if not hasattr(AppKit, "NSUserNotificationCenter"):
		print "macNotificationsMain: NSUserNotificationCenter not available. this is only available since MacOSX 10.8"
		return
	
	pool = AppKit.NSAutoreleasePool.alloc().init()

	appDelegate = AppKit.NSApplication.sharedApplication().delegate()	
	notifCenter = AppKit.NSUserNotificationCenter.defaultUserNotificationCenter()
	notifCenter.setDelegate_(appDelegate)

	def notifyCurSong():
		notif = AppKit.NSUserNotification.alloc().init()
		notif.setTitle_("MusicPlayer")
		song = state.curSong
		s = None
		try:
			s = utils.convertToUnicode(song.userString)
		except: pass
		notif.setInformativeText_(s)
		notifCenter.deliverNotification_(notif)
		#print "notification:", notif

	for ev,args,kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onSongChange:
			notifyCurSong()
		elif ev is PlayerEventCallbacks.onPlayingStateChange and kwargs["newState"] == True:
			notifyCurSong()

	del pool

def linuxNotificationsMain():
	from State import state
	from player import PlayerEventCallbacks
	from utils import convertToUnicode

	try:
		import pynotify
	except ImportError:
		return

	def notifyCurSong():
		pynotify.init("MusicPlayer")
		song = state.curSong
		s = None
		try:
			s = convertToUnicode(song.userString)
		except: pass

		notif = pynotify.Notification(s)
		notif.show()
		#print "notification:", notif

	for ev, args, kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onSongChange:
			notifyCurSong()
		elif ev is PlayerEventCallbacks.onPlayingStateChange and kwargs["newState"] == True:
			notifyCurSong()

	del pool

def notificationsMain():
	import sys
	if sys.platform == "darwin":
		macNotificationsMain()
	elif sys.platform == "linux2":
		linuxNotificationsMain()
	else:
		print "no notification implementation"
