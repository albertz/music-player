

from Song import Song

def randomFileQueueGen():
	import os
	from RandomFileQueue import RandomFileQueue
	fileQueue = RandomFileQueue(
		rootdir = os.path.expanduser("~/Music"),
		fileexts = ["mp3", "ogg", "flac", "wma"])
	while True:
		f = fileQueue.getNextFile()
		yield Song(f)

from collections import deque
from threading import Lock

class MainQueue:
	def __init__(self):
		self.lock = Lock()
		self.manualQueue = deque()
		self.infiniteQueue = randomFileQueueGen()

	def getNextSong(self):
		with self.lock:
			if self.manualQueue:
				return self.manualQueue.popleft()
			return next(self.infiniteQueue)

	def fillUpTo(self, n=10):
		with self.lock:
			while len(self.manualQueue) < n:
				self.manualQueue.append(next(self.infiniteQueue))

queue = MainQueue()

def getNextSong():
	return queue.getNextSong()

def queueMain():
	# TODO: preload, etc.
	pass
