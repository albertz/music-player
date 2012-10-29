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
		lastfm.onSongFinished(song)

def tracker_lastfmMain():
	if not appinfo.config.lastFm: return

	lastfm.login()
	for ev,args,kwargs in state.updates.read(
		listType = lambda: PersistentObject(deque, "lastfm-queue.dat", namespace=globals())
	):
		try:
			track(ev, args, kwargs)
		except:
			sys.excepthook(*sys.exc_info())
	lastfm.quit()
