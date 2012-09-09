
from Song import Song
from State import state
from player import PlayerEventCallbacks
from utils import *
import math, random
import appinfo

class RandomFileQueueGen:
	randomQuality = 0.5

	def __init__(self, dir):
		import os
		from RandomFileQueue import RandomFileQueue
		self.fileQueue = RandomFileQueue(
			rootdir = os.path.expanduser(dir),
			fileexts = appinfo.formats)

	def next(self):
		return self.fileQueue.getNextFile()

	def __iter__(self):
		while True:
			yield self.next()

class RandomFromSongDatabase:
	randomQuality = 0.0

	def __init__(self):
		from SongDatabase import SongDatabase
		self.database = SongDatabase(appinfo.musicdatabase)
		self.database.initDatabase()

		def loadDatabase():
			for dir in appinfo.musicdirs:
				self.database.addSongsFromDirectory(dir)

			self.randomQuality = 0.5
			print "Done loading songs"

			self.database.update()

			print "Done updating database"
			self.randomQuality = 1

		from threading import Thread
		loadDatabaseThread = Thread(target=loadDatabase, name="loadDatabase")
		loadDatabaseThread.start()

	def next(self):
		try:
			oldSong = state.recentlyPlayedList.getLastN(1)[0]
		except:
			oldSong = None
		return next(iter(self.database.getRandomSongs(oldSong=oldSong, limit=1)))

	def __iter__(self):
		while True:
			yield self.next()


class RandomSongs:
	randomQuality = 0.5
	def __init__(self, generators):
		self.generators = [gen() for gen in generators]
	def next(self):
		while True:
			generators = list(self.generators)
			if not generators:
				raise StopIteration
			qualitySum = sum([gen.randomQuality for gen in generators])
			self.randomQuality = qualitySum / len(generators)
			r = random.random() * qualitySum
			i = 0
			gen = generators[i]
			while i < len(generators)-1 and r > gen.randomQuality:
				r -= gen.randomQuality
				i += 1
				gen = generators[i]
			try:
				return next(gen)
			except StopIteration:
				#print "warning: generator", gen, "raised StopIteration"
				#sys.excepthook(*sys.exc_info())
				pass
			generators.pop(i)
	def __iter__(self):
		while True:
			yield self.next()

from collections import deque
from threading import Lock

class InfQueue:
	def __init__(self):
		self.generator = RandomSongs([
			RandomFromSongDatabase,
			lambda: RandomSongs([
				(lambda: RandomFileQueueGen(dir)) for dir in appinfo.musicdirs])
		])
		self.checkNextNForBest = 10
		self.checkLastNForContext = 10

	def calcContextMatchScore(self, song):
		count = 0
		lastSongs = state.recentlyPlayedList.getLastN(self.checkLastNForContext)
		lastSongs = filter(lambda s: not s.skipped, lastSongs)
		if not lastSongs: return 0.0
		for lastSong in lastSongs:
			count += max(intersectFuzzySets(song.tags, lastSong.tags).values() + [0])
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
