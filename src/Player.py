

try:
	PlayerEventCallbacks
except NameError:
	# This is fixed. In case we add some, we have to restart.
	class PlayerEventCallbacks:
		onSongChange = None
		onSongFinished = None
		onPlayingStateChange = None

def songsQueue(state):
	import sys
	if state.curSong:
		# We just started the player and we have a current song from persistent storage.
		# Yield it now so that we begin playing with this song.
		# Yield the Song object itself, though, not the ObjectProxy. The ObjectProxy
		# would result in very strange behavior later for onSongChange events.
		try:
			song = state.curSong.__get__(None)
			assert song
			song.openFile()
		except Exception:
			print "exception in songsQueue on getting first song"
			sys.excepthook(*sys.exc_info())
		else:
			yield song
	import Queue
	while True:
		try:
			song = Queue.getNextSong()
			assert song
			song.openFile()
		except Exception:
			print "exception in songsQueue on getting next song"
			sys.excepthook(*sys.exc_info())
		else:
			yield song

def songsPeekQueue():
	def openSong(song):
		song.openFile()
		return song
	import Queue
	return lambda n: filter(openSong, Queue.peekNextSongs(n))

# This is an special extra callback.
# This is called very first. We do this so that
# we always have state.curSong right.
def onSongChange(**kwargs):
	from State import state
	state.curSong = kwargs["newSong"]

def initEventCallbacks():
	from State import state
	from Events import EventCallback
	for e in [m for m in dir(PlayerEventCallbacks) if not m.startswith("_")]:
		if getattr(PlayerEventCallbacks, e): continue
		cb = EventCallback(targetQueue=state.updates, name=e, reprname="PlayerEventCallbacks.%s" % e)
		if e == "onSongChange":
			cb.extraCall = onSongChange
		setattr(PlayerEventCallbacks, e, cb)

initEventCallbacks()

def loadPlayer(state):
	import musicplayer

	from appinfo import args, config
	import TaskSystem
	if args.debug and TaskSystem.isMainProcess:
		musicplayer.enableDebugLog(True)

	player = musicplayer.createPlayer()
	player.outSamplerate = config.sampleRate
	player.preferredSoundDevice = config.preferredSoundDevice
	for e in [m for m in dir(PlayerEventCallbacks) if not m.startswith("_")]:
		cb = getattr(PlayerEventCallbacks, e)
		assert cb
		setattr(player, e, cb)
	player.queue = songsQueue(state)
	player.peekQueue = songsPeekQueue()
	player.volume = state.volume

	player.startWorkerThread()

	return player
