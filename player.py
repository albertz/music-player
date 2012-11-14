# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.
from utils import *

try:
	PlayerEventCallbacks
except NameError:
	# This is fixed. In case we add some, we have to restart.
	class PlayerEventCallbacks:
		onSongChange = None
		onSongFinished = None
		onPlayingStateChange = None
	
def songs(state):
	if state.curSong:
		# We just started the player and we have a current song from persistent storage.
		# Yield it now so that we begin playing with this song.
		# Yield the Song object itself, though, not the ObjectProxy. The ObjectProxy
		# would result in very strange behavior later for onSongChange events.
		song = state.curSong.__get__(None)
		assert song
		song.openFile()
		yield song
	import queue
	while True:
		song = queue.getNextSong()
		assert song
		song.openFile()
		yield song

# This is an special extra callback.
# This is called very first. We do this so that
# we always have state.curSong right.
def onSongChange(**kwargs):
	from State import state
	state.curSong = kwargs["newSong"]

def loadPlayer(state):
	import ffmpeg
	player = ffmpeg.createPlayer()
	for e in [m for m in dir(PlayerEventCallbacks) if not m.startswith("_")]:
		cb = EventCallback(targetQueue=state.updates, name=e)
		if e == "onSongChange":
			cb.extraCall = onSongChange
		setattr(PlayerEventCallbacks, e, cb)
		setattr(player, e, cb)
	player.queue = songs(state)
	player.volume = state.volume
	return player

def playerMain():
	from State import state
	#state.player.playing = True
	for ev,args,kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onSongChange:
			state.curSong.save()
			oldSong = kwargs["oldSong"]
			if oldSong:
				if kwargs["skipped"]: oldSong.skipped = True
				state.recentlyPlayedList.append(oldSong)
				state.recentlyPlayedList.save()
		pass # onPlayingStateChange
