#!/usr/bin/python

import better_exchook
better_exchook.install()

from utils import *
from pprint import pprint

mainStateChanges = OnRequestQueue()

player = None

class PlayerEventCallbacks:
	onSongChange = None
	onSongFinished = None
	onPlayingStateChange = None

def playerMain():
	global player
	import ffmpeg
	player = ffmpeg.createPlayer()
	for e in [m for m in dir(PlayerEventCallbacks) if not m.startswith("_")]:
		cb = EventCallback(targetQueue=mainStateChanges, name=e)
		setattr(PlayerEventCallbacks, e, cb)
		setattr(player, e, cb)
	player.queue = state.queue
	player.playing = True
	# install some callbacks in player, like song changed, etc
	for ev in mainStateChanges.read():
		pass

import lastfm
	
def track(event, args, kwargs):
	print "track:", repr(event), repr(args), repr(kwargs)
	if event is PlayerEventCallbacks.onSongChange:
		newSong = kwargs["newSong"]
		if "artist" not in newSong.metadata:
			print "new song metadata is incomplete:", newSong.metadata
		else:
			print "new song:", newSong.fileext, ",", newSong.artist, "-", newSong.track, ",", formatTime(newSong.duration)
			pprint(newSong.metadata)
		doAsync(lambda: lastfm.onSongChange(newSong))
	if event is PlayerEventCallbacks.onSongFinished:
		song = kwargs["song"]
		doAsync(lambda: lastfm.onSongFinished(song))
	
def trackerMain():
	for ev,args,kwargs in mainStateChanges.read():
		try:
			track(ev, args, kwargs)
		except:
			sys.excepthook(*sys.exc_info())

def onMediaKeyUp(control):
	try:
		if control == "play-pause":
			player.playing = not player.playing
		elif control == "next":
			player.nextSong()
	except:
		sys.excepthook(*sys.exc_info())

def mediakeysMain():
	import mediakeys
	eventTap = mediakeys.EventListener()
	eventTap.onMediaKeyUp = onMediaKeyUp
	eventTap.start()
	for ev in mainStateChanges.read(): pass
	eventTap.stop()
	
class Actions:
	def play(self, song):
		# via ffmpeg or so. load dynamically (ctypes)
		pass
		
	def pause(self): pass
	def next(self): pass
	def forward10s(self): pass

actions = Actions()

from State import State
state = State(globals())

if __name__ == '__main__':
	lastfm.login()
	
	import time, os, sys
	loopFunc = lambda: time.sleep(10)
	if os.isatty(sys.stdin.fileno()):
		# If we are a TTY, do some very simple input handling.
		setTtyNoncanonical(sys.stdin.fileno())
		def handleInput():
			global player
			ch = os.read(sys.stdin.fileno(),7)
			if ch == "q": sys.exit(0)
			try:
				if ch == "\x1b[D": # left
					player.seekRel(-10)
				elif ch == "\x1b[C": #right
					player.seekRel(10)
				elif ch == "\n": # return
					player.nextSong()
				elif ch == " ":
					player.playing = not player.playing
			except:
				sys.excepthook(*sys.exc_info())
		loopFunc = handleInput
		
	from threading import Thread
	threads = []
	threads += [Thread(target=playerMain, name="Player")]
	threads += [Thread(target=trackerMain, name="Tracker")]
	threads += [Thread(target=mediakeysMain, name="Mediakeys")]
	for t in threads: t.start()
	while True:
		try: loopFunc() # wait for KeyboardInterrupt
		except BaseException, e:
			mainStateChanges.put((e, (), {}))
			mainStateChanges.cancelAll()
			break
	for t in threads: t.join()
	
	