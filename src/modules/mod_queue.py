# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

def queueMain():
	from Player import PlayerEventCallbacks
	from Queue import queue
	from State import state

	queue.fillUpTo() # add some right away if empty...
	for ev, args, kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onSongChange:
			queue.fillUpTo()
