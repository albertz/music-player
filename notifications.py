def macNotificationsMain():
	from State import state
	from player import PlayerEventCallbacks
	import AppKit
	import utils
	
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

def notificationMain():
	import sys
	if sys.platform == "darwin":
		macNotificationMain()
	else:
		print "no notification implementation"
