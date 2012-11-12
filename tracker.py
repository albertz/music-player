
from utils import *
import sys, time

from State import state
from player import PlayerEventCallbacks

import appinfo

def track(event, args, kwargs):
	#print "track:", repr(event), repr(args), repr(kwargs)
	if event is PlayerEventCallbacks.onSongChange:
		oldSong = kwargs["oldSong"]
		newSong = kwargs["newSong"]
		print "new song:", newSong.userLongString.encode("utf-8")
		if oldSong: oldSong.close() # in case anyone is holding any ref to it, close at least the file

		if kwargs["skipped"] and oldSong: oldSong.update("skipCount", lambda n: n+1, default=0)
		if oldSong: oldSong.lastPlayedDate = time.time()

	if event is PlayerEventCallbacks.onSongFinished:
		song = kwargs["song"]
		song.update("completedCount", lambda n: n+1, default=0)
		
def trackerMain():
	for ev,args,kwargs in state.updates.read():
		try:
			track(ev, args, kwargs)
		except:
			sys.excepthook(*sys.exc_info())
