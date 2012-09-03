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
			notif.setInformativeText_(kwargs["newSong"].userString)
			notifCenter.deliverNotification_(notif)
			#print "notification:", notif

	del pool
