def notificationsMain():
	from State import state
	from player import PlayerEventCallbacks
	import AppKit

	pool = AppKit.NSAutoreleasePool.alloc().init()

	appDelegate = AppKit.NSApplication.sharedApplication().delegate()
	notifCenter = AppKit.NSUserNotificationCenter.defaultUserNotificationCenter()
	notifCenter.setDelegate_(appDelegate)

	for ev,args,kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onSongChange:
			notif = AppKit.NSUserNotification.alloc().init()
			notif.setTitle_("MusicPlayer")
			newSong = kwargs["newSong"]
			s = newSong.userString
			try:
				s = s.decode("utf-8")
			except:
				s = str(s)
			notif.setInformativeText_(s)
			notifCenter.deliverNotification_(notif)
			#print "notification:", notif

	del pool
