# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.
""" This is the Last.fm tracker module. """

from utils import *
import sys

from State import state
from player import PlayerEventCallbacks

import appinfo
import lastfm

def track(event, args, kwargs):
	if event is PlayerEventCallbacks.onSongChange:
		oldSong = kwargs["oldSong"]
		newSong = kwargs["newSong"]
		lastfm.onSongChange(newSong)
	if event is PlayerEventCallbacks.onSongFinished:
		song = kwargs["song"]
		timestamp = kwargs["timestamp"]
		lastfm.onSongFinished(song, timestamp=timestamp)

def tracker_lastfmMain():
	if not appinfo.config.lastFm: return

	stateUpdateStream = state.updates.read(
		listType = lambda: PersistentObject(
			deque, "lastfm-queue.dat", namespace=globals(),
			installAutosaveWrappersOn=OnRequestQueue.ListUsedFunctions)
	)

	lastfm.login()
	for ev,args,kwargs in stateUpdateStream:
		try:
			track(ev, args, kwargs)
		except Exception:
			sys.excepthook(*sys.exc_info())
	lastfm.quit()
