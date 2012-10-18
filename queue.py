from Song import Song
from State import state
from player import PlayerEventCallbacks
from utils import *
import Traits
import math, random
import appinfo


try:
	QueueCallbacks
except NameError:
	# This is fixed. In case we add some, we have to restart.
	class QueueCallbacks:
		onModify = Id("onModify")


def putOnModify(*args, **kwargs):
	state.updates.put((QueueCallbacks.onModify, args, kwargs))

class RandomFileQueueGen:
	randomQuality = 0.5

	def __init__(self, dir):
		import os
		from RandomFileQueue import RandomFileQueue

		self.fileQueue = RandomFileQueue(
			rootdir=os.path.expanduser(dir),
			fileexts=appinfo.formats)

	def next(self):
		return self.fileQueue.getNextFile()


class RandomFromSongDatabaseGen:
	randomQuality = 0.0

	def __init__(self):
		def loadDatabase():
			from SongStore import SongStore
			self.database = SongStore()

			import utils

			print "updating database"

			for dir in appinfo.musicdirs:
				self.database.addMany(utils.getSongsFromDirectory(dir))

			self.randomQuality = 0.5
			print "Done loading songs"

		from threading import Thread

		loadDatabaseThread = Thread(target=loadDatabase, name="loadDatabase")
		loadDatabaseThread.start()

	def next(self):
		try:
			oldSong = state.recentlyPlayedList.getLastN(1)[0]
		except:
			oldSong = None

		songs = self.database.getRandomSongs(oldSong=oldSong, limit=1)

		return next(iter(songs))



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
			while i < len(generators) - 1 and r > gen.randomQuality:
				r -= gen.randomQuality
				i += 1
				gen = generators[i]
			try:
				return next(gen)
			#except StopIteration:
				#print "warning: generator", gen, "raised StopIteration"
				#sys.excepthook(*sys.exc_info())
				#pass
			except: # just catch any exception, esp non-StopIteration
				print "RandomSongs generator raised exception"
				sys.excepthook(*sys.exc_info())
			generators.pop(i)

	def __iter__(self):
		while True:
			yield self.next()

from collections import deque
from threading import RLock

class ListWrapper: # implements the List trait
	def __init__(self, owner, list): # parent is supposed to be the MainQueue
		self.owner = owner
		self.lock = owner.lock
		self.list = list
	
	def onInsert(self, index, value): pass
	def onRemove(self, index): pass
	def onClear(self): pass
	
	def insert(self, index, value):
		with self.lock:
			self.list.insert(index, value)
			self.onInsert(index, value)
			self.list.save()
		putOnModify()
	def remove(self, index):
		with self.lock:
			del self.list[index]
			self.onRemove(index)
			self.list.save()
		putOnModify()
	def popleft(self):
		with self.lock:
			obj = self.list.pop(0)
			self.onRemove(0)
			self.list.save()
			return obj
		putOnModify()
	def append(self, value):
		with self.lock:
			self.list.append(value)
			self.onInsert(len(self.list)-1, value)
			self.list.save()
		putOnModify()
	def clear(self):
		with self.lock:
			self.list.clear()
			self.onClear()
			self.list.save()
		putOnModify()
	def __getitem__(self, index):
		with self.lock:
			return self.list[index]
	def __len__(self):
		with self.lock:
			return len(self.list)
			
class MainQueue:
	def __init__(self):
		self.lock = RLock()

		self.generator = RandomSongs([
			#RandomFromSongDatabaseGen, # no good way right now ...
			lambda: RandomSongs([
			(lambda: RandomFileQueueGen(dir)) for dir in appinfo.musicdirs])
		])
		self.checkNextNForBest = 10
		self.checkLastNForContext = 10
		self.checkLastInQueueNForContext = 2

	def queueDragHandler(self, queue, index, files):
		def doInsert(index=index):
			for fn in files:
				queue.insert(index, Song(fn))
				index += 1
		from threading import Thread
		t = Thread(target=doInsert, name="queueDragHandler")
		t.daemon = True
		t.start()
		return True

	@UserAttrib(type=Traits.List, variableHeight=True, canHaveFocus=True, dragHandler=queueDragHandler)
	@initBy
	def queue(self):
		l = PersistentObject(list, "queue.dat", namespace=globals())
		return ListWrapper(self, l)
		
	def getNextSong(self):
		with self.lock:
			if len(self.queue) > 0:
				return self.queue.popleft()
		return getNextSong_auto()

	def peekNextN(self, n): # only from self.queue, no adding! might return less
		with self.lock:
			return [self.queue[i] for i in range(min(n, len(self.queue)))]

	def calcContextMatchScore(self, song):
		count = 0
		lastSongs = []
		with self.lock:
			lastSongs += [self.queue[-i] for i in range(1,min(self.checkLastInQueueNForContext,len(self.queue))+1)]
		lastSongs += state.recentlyPlayedList.getLastN(self.checkLastNForContext)
		lastSongs = filter(lambda s: not getattr(s, "skipped", False), lastSongs)
		if not lastSongs: return 0.0
		for lastSong in lastSongs:
			count += max(intersectFuzzySets(song.tags, lastSong.tags).values() + [0])
		s = float(count) / (self.checkLastNForContext + self.checkLastInQueueNForContext)
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

	def getNextSong_auto(self):
		filenames = takeN(self.generator, self.checkNextNForBest)
		songs = map(Song, filenames)
		scores = map(lambda song: (self.calcScore(song), song), songs)
		best = max(scores)
		song = best[1]
		return song

	@UserAttrib(type=Traits.Action)
	def clear(self):
		self.queue.clear()
			
	@UserAttrib(type=Traits.Action)
	def fillUpTo(self, n=10):
		while True:
			with self.lock:
				if len(self.queue) >= n: break
			nextSong = self.getNextSong_auto()
			self.queue.append(nextSong)

	@UserAttrib(type=Traits.Action)
	def addSome(self, n=10):
		for i in xrange(n):
			nextSong = self.getNextSong_auto()
			self.queue.append(nextSong)

queue = MainQueue()

def getNextSong():
	return queue.getNextSong()

def queueMain():
	queue.fillUpTo() # add some right away if empty...
	for ev, args, kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onSongChange:
			queue.fillUpTo()
