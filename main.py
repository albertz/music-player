#!/usr/bin/python

import better_exchook
better_exchook.install()

from utils import *
from pprint import pprint

from State import state, playerMain, PlayerEventCallbacks
	
import lastfm

def track(event, args, kwargs):
	print "track:", repr(event), repr(args), repr(kwargs)
	if event is PlayerEventCallbacks.onSongChange:
		oldSong = kwargs["oldSong"]
		if oldSong: oldSong.close() # in case anyone is holding any ref to it, close at least the file
		newSong = kwargs["newSong"]
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

def onMediaKeyUp(control):
	try:
		if control == "play-pause":
			state.player.playing = not state.player.playing
		elif control == "next":
			state.player.nextSong()
	except:
		sys.excepthook(*sys.exc_info())

def mediakeysMain():
	import mediakeys
	eventTap = mediakeys.EventListener()
	eventTap.onMediaKeyUp = onMediaKeyUp
	eventTap.start()
	for ev in state.updates.read(): pass # wait for exit
	eventTap.stop()
	
class Actions:
	def play(self): state.player.playing = True
	def pause(self): state.player.playing = False
	def next(self): state.player.nextSong()
	def forward10s(self): state.player.seekRel(10)

actions = Actions()


if __name__ == '__main__':	
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
					state.player.seekRel(-10)
				elif ch == "\x1b[C": #right
					state.player.seekRel(10)
				elif ch == "\n": # return
					state.player.nextSong()
				elif ch == " ":
					state.player.playing = not state.player.playing
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
			state.updates.put((e, (), {}))
			state.updates.cancelAll()
			break
	for t in threads: t.join()
	
	