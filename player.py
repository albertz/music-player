from utils import *

class PlayerEventCallbacks:
	onSongChange = None
	onSongFinished = None
	onPlayingStateChange = None

def loadPlayer(state):
	import ffmpeg
	player = ffmpeg.createPlayer()
	for e in [m for m in dir(PlayerEventCallbacks) if not m.startswith("_")]:
		cb = EventCallback(targetQueue=state.updates, name=e)
		setattr(PlayerEventCallbacks, e, cb)
		setattr(player, e, cb)
	player.queue = state.queue
	return player

def playerMain():
	from State import state
	#state.player.playing = True
	for ev,args,kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onSongChange:
			state.curSong = kwargs["newSong"]
			state.curSong.save()
			state.recentlyPlayedList.append(kwargs["oldSong"])
			state.recentlyPlayedList.save()
		pass # onPlayingStateChange
