
from Song import Song
from State import state
from player import PlayerEventCallbacks
from utils import *
import math, random
import appinfo

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

class NextSongAlgorithm:

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
		scores += [self.calcRating(song) * random.gauss(1, 0.5)]
		scores += [self.calcContextMatchScore(song) * random.gauss(1, 0.5)]
		return sum(scores) + random.gauss(1, 0.5)

	def getNextSong(self, songs):
		scores = map(lambda song: (self.calcScore(song), song), songs)
		best = max(scores)
		song = best[1]
		return song

	@property
	def checkNextNForBest(self):
		return 10

	@property
	def checkLastNForContext(self):
		return 10


class InfQueue:
	def __init__(self):
		self.generator = randomFileQueueGen()
		self.nextSongAlgorithm = NextSongAlgorithm()

		self.checkNextNForBest = 10
		self.checkLastNForContext = 10

	def getNextSong(self):
		filenames = takeN(self.generator, self.nextSongAlgorithm.checkNextNForBest)
		songs = map(Song, filenames)
		return self.nextSongAlgorithm.getNextSong(songs)



from SongDatabase import SongDatabase

class InfDatabaseQueue:
	def __init__(self):
		self.database = SongDatabase(appinfo.musicdir, appinfo.formats, appinfo.musicdatabase)
		self.database.fillDatabase()
		self.nextSongAlgorithm = NextSongAlgorithm()

	def getNextSong(self):
		oldSong = state.recentlyPlayedList.getLastN(1)[0]
		return self.nextSongAlgorithm.getNextSong(self.database.getRandomSongs(oldSong=oldSong, limit=self.nextSongAlgorithm.checkLastNForContext))

class MainQueue:
	def __init__(self):
		self.lock = Lock()
		self.manualQueue = deque()
		self.infiniteQueue = InfDatabaseQueue()

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
