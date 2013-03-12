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

def event_filter(ev):
	if ev is PlayerEventCallbacks.onSongChange: return True
	if ev is PlayerEventCallbacks.onSongFinished: return True
	return False

def stateUpdates_append_wrapper(self, value):
	value = ev,args,kwargs
	if not event_filter(ev): return
	self.__get__(None).append(value)
	self.save()

def tracker_lastfmMain():
	if not appinfo.config.lastFm: return

	assert "append" in OnRequestQueue.ListUsedModFunctions
	
	queueList = PersistentObject(
		deque, "lastfm-queue.dat", namespace=globals(),
		customAttribs = {"append": stateUpdates_append_wrapper},
		)
	
	stateUpdateStream = state.updates.read(queueList=queueList)

	lastfm.login()
	for ev,args,kwargs in stateUpdateStream:
		try:
			track(ev, args, kwargs)
		except Exception:
			sys.excepthook(*sys.exc_info())
		else:
			queueList.save()			
	lastfm.quit()
