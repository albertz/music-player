#!/usr/bin/python

from utils import *

mainStateChanges = OnRequestQueue()

def main():
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
	
def tracker():
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
	from threading import Thread
	threads = []
	threads += [Thread(target=main, name="Main")]
	threads += [Thread(target=tracker, name="Tracker")]
	for t in threads: t.start()
	import time
	while True:
		try: time.sleep(10) # wait for KeyboardInterrupt
		except BaseException, e:
			mainStateChanges.put(e)
			mainStateChanges.cancelAll()
			break
	for t in threads: t.join()
	
	