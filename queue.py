
from Song import Song
from State import state
from player import PlayerEventCallbacks
from utils import *
import math

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
		self.checkLastNForContext = 10
	def calcContextMatchScore(self, song):
		count = 0
		for lastSong in state.recentlyPlayedList.getLastN(self.checkLastNForContext):
			count += 1 if bool(set(song.tags) & set(lastSong.tags)) else 0
		s = float(count) / self.checkLastNForContext
		# We likely get small values here. Boost a bit but keep in [0,1] range. sqrt is a good fit.
		return math.sqrt(s)
	def calcRating(self, song):
		import rating
		song.rating = rating.getRating(song.url, default=0.0)
		return song.rating
	def calcScore(self, song):
		scores = []
		scores += [self.calcRating(song)]
		scores += [self.calcContextMatchScore(song)]
		return sum(scores)
	def getNextSong(self):
		filenames = takeN(self.generator, self.checkNextNForBest)
		songs = map(Song, filenames)
		scores = map(lambda song: (self.calcScore(song), song), songs)
		best = max(scores)
		song = best[1]
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
