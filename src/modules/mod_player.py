# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.


def playerMain():
	from Player import PlayerEventCallbacks
	from State import state
	for ev,args,kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onPlayingStateChange:
			state.__class__.playPause.updateEvent(state).push()
		elif ev is PlayerEventCallbacks.onSongChange:
			state.curSong.save()
			oldSong = kwargs["oldSong"]
			if oldSong:
				if kwargs["skipped"]: oldSong.skipped = True
				state.recentlyPlayedList.append(oldSong)
				state.recentlyPlayedList.save()
