
from utils import *
from pprint import pprint
import sys

from State import state
from player import PlayerEventCallbacks

import lastfm

def track(event, args, kwargs):
	print "track:", repr(event), repr(args), repr(kwargs)
	if event is PlayerEventCallbacks.onSongChange:
		oldSong = kwargs["oldSong"]
		newSong = kwargs["newSong"]
		if oldSong: oldSong.close() # in case anyone is holding any ref to it, close at least the file
		if "artist" not in newSong.metadata:
			print "new song metadata is incomplete:", newSong.metadata
		else:
			print "new song:", newSong.fileext, ",", newSong.artist, "-", newSong.track, ",", formatTime(newSong.duration)
			pprint(newSong.metadata)
		lastfm.onSongChange(newSong)
	if event is PlayerEventCallbacks.onSongFinished:
		song = kwargs["song"]
		lastfm.onSongFinished(song)

def trackerMain():
	lastfm.login()
	for ev,args,kwargs in state.updates.read():
		try:
			track(ev, args, kwargs)
		except:
			sys.excepthook(*sys.exc_info())
	lastfm.quit()
