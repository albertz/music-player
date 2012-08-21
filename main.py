#!/usr/bin/python

#from Queue import Queue
from collections import deque
from threading import Event, Lock
class OnRequestQueue:
	class QueueEnd:
		def __init__(self):
			self.q = deque()
			self.putEv = Event()
			self.lock = Lock()
	def __init__(self):
		self.queues = set()
	def put(self, item):
		for q in self.queues:
			with q.lock:
				q.q.append(item)
				q.putEv.set()
	def read(self):
		q = self.QueueEnd()
		self.queues.add(q)
		while q.putEv.wait():
			with q.lock:
				l = list(q.q)
				q.q.clear()
				q.putEv.clear()
			for item in l:
				yield item

mainStateChanges = OnRequestQueue()

def main():
	import ffmpeg
	player = ffmpeg.createPlayer()
	player.queue = state.queue
	player.playing = True
	# install some callbacks in player, like song changed, etc
	for ev in mainStateChanges.read():
		print ev
	
def track(event):
	# Last.fm or so
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

class initBy(property):
	def __init__(self, initFunc):
		property.__init__(self, fget = self.fget)
		self.initFunc = initFunc
	def fget(self, inst):
		if hasattr(self, "value"): return self.value
		self.value = self.initFunc()
		return self.value

class oneOf(property):
	def __init__(self, *consts):
		property.__init__(self, fget = self.fget, fset = self.fset)
		assert len(consts) > 0
		self.consts = consts
		self.value = consts[0]
	def fget(self, inst):
		return self
	def fset(self, inst, value):
		assert value in self.consts
		self.value = value
		
def loadQueue():
	print "load queue"

	# dummy example from test_ffmpeg
	def songs():
		class Song:
			def __init__(self, fn):
				self.url = fn
				self.f = open(fn)
			def readPacket(self, bufSize):
				s = self.f.read(bufSize)
				return s
			def seekRaw(self, offset, whence):
				r = self.f.seek(offset, whence)
				return self.f.tell()
		files = [
			"/Users/az/Music/Classic/Glenn Gould Plays Bach/Two- & Three-Part Inventions - Gould/19 Bach - Invention 13 in a (BWV 784).mp3",
			"/Users/az/Music/Rock/Tool/Lateralus/09 Lateralus.flac",
			"/Users/az/Music/Cults - Cults 7/Cults - Cults 7- - 03 The Curse.flac",
			"/Users/az/Music/Special/zorba/(01) - Theme From Zorba The Greek.ogg",
			"/Users/az/Music/Classic/Glenn Gould Plays Bach/French Suites, BWV812-7 - Gould/Bach, French Suite 5 in G, BWV816 - 5 Bourree.mp3",
			"/Users/az/Music/Electronic/Von Paul Kalkbrenner - Aaron.mp3",
			"/Users/az/Music/Electronic/One Day_Reckoning Song (Wankelmut Remix) - Asaf Avidan & the Mojos.mp3",
		]
		i = 0
		while True:
			yield Song(files[i])
			i += 1
			if i >= len(files): i = 0
	return songs()
	
def loadRecentlyplayedList():
	pass

class State:
	queue = initBy(loadQueue)
	recentlyPlayedList = initBy(loadRecentlyplayedList)
	
	playState = oneOf(
		"playing",
		"paused"
	)
	
state = State()

if __name__ == '__main__':
	import thread
	thread.start_new_thread(tracker, ())
	main()
	