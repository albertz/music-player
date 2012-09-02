
from Song import Song
from State import state
from player import PlayerEventCallbacks
from utils import *

def randomFileQueueGen(dir="~/Music"):
	import os
	from RandomFileQueue import RandomFileQueue
	fileQueue = RandomFileQueue(
		rootdir = os.path.expanduser(dir),
		fileexts = ["mp3", "ogg", "flac", "wma"])
	while True:
		yield fileQueue.getNextFile()

from collections import deque
from threading import Lock

class InfQueue:
	def __init__(self):
		self.generator = randomFileQueueGen()
		self.checkNextNForBest = 10
	def getNextSong(self):
		import rating
		filenames = takeN(self.generator, self.checkNextNForBest)
		ratings = map(lambda fn: (rating.getRating(fn, default=0.0), fn), filenames)
		best = max(ratings)
		song = Song(best[1])
		song.rating = best[0]
		return song

class MainQueue:
	def __init__(self):
		self.lock = Lock()
		self.manualQueue = deque()
		self.infiniteQueue = InfQueue()

	def getNextSong(self):
		with self.lock:
			if self.manualQueue:
				return self.manualQueue.popleft()
			return self.infiniteQueue.getNextSong()

	def fillUpTo(self, n=10):
		with self.lock:
			while len(self.manualQueue) < n:
				self.manualQueue.append(self.infiniteQueue.getNextSong())

queue = MainQueue()

def getNextSong():
	return queue.getNextSong()

def queueMain():
	for ev,args,kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onSongChange:
			queue.fillUpTo()
