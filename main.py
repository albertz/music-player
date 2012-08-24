#!/usr/bin/python

from utils import *

mainStateChanges = OnRequestQueue()

player = None

def playerMain():
	global player
	import ffmpeg
	player = ffmpeg.createPlayer()
	for e in ("onSongChange", "onSongFinished", "onPlayingStateChange"):
		setattr(player, e, EventCallback(targetQueue=mainStateChanges, name=e))
	player.queue = state.queue
	player.playing = True
	# install some callbacks in player, like song changed, etc
	for ev in mainStateChanges.read():
		pass
	
def track(event):
	# Last.fm or so
	print "track:", repr(event)
	pass
	
def trackerMain():
	for ev in mainStateChanges.read():
		track(ev)

class Actions:
	def play(self, song):
		# via ffmpeg or so. load dynamically (ctypes)
		pass
		
		
	def pause(self): pass
	def next(self): pass
	def forward10s(self): pass

actions = Actions()

from State import State
state = State()

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
	for t in threads: t.start()
	while True:
		try: loopFunc() # wait for KeyboardInterrupt
		except BaseException, e:
			mainStateChanges.put(e)
			mainStateChanges.cancelAll()
			break
	for t in threads: t.join()
	
	