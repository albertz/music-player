def notificationsMain():
	from State import state
	from player import PlayerEventCallbacks
	import AppKit

	pool = AppKit.NSAutoreleasePool.alloc().init()

	appDelegate = AppKit.NSApplication.sharedApplication().delegate()
	notifCenter = AppKit.NSUserNotificationCenter.defaultUserNotificationCenter()
	notifCenter.setDelegate_(appDelegate)

	def notifyCurSong():
		notif = AppKit.NSUserNotification.alloc().init()
		notif.setTitle_("MusicPlayer")
		song = state.player.curSong
		try:
			s = None
			s = song.userString
			s = s.decode("utf-8")
		except:
			s = str(s)
		notif.setInformativeText_(s)
		notifCenter.deliverNotification_(notif)
		#print "notification:", notif

	for ev,args,kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onSongChange:
			notifyCurSong()
		elif ev is PlayerEventCallbacks.onPlayingStateChange and kwargs["newState"] == True:
			notifyCurSong()

	del pool
