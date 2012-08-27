from utils import *
from Song import Song
import appinfo

def loadQueue(state):
	print "load queue"
	
	def songs():
		import os
		from RandomFileQueue import RandomFileQueue
		fileQueue = RandomFileQueue(
			rootdir = os.path.expanduser("~/Music"),
			fileexts = ["mp3", "ogg", "flac", "wma"])
		while True:
			f = fileQueue.getNextFile()
			yield Song(f)
			
	return songs()
	
from collections import deque

class RecentlyplayedList:
	Limit = 10
	def __init__(self, list=[], previous=None):
		self.list = deque(list)
		self.previous = None
	def append(self, song):
		self.list.append(song)
		if len(self.list) >= self.Limit:
			newList = RecentlyplayedList(list=self.list, previous=self.previous)
			self.previous = newList
			self.list = deque()
	def __repr__(self):
		return "RecentlyplayedList(list=%s, previous=%s)" % (
			betterRepr(self.list),
			betterRepr(self.previous))

def loadRecentlyplayedList(state):
	return PersistentObject(RecentlyplayedList, "recentlyplayed.dat")

class State:
	queue = initBy(loadQueue)
	recentlyPlayedList = initBy(loadRecentlyplayedList)
	curSong = None
	
	playState = oneOf(
		"playing",
		"paused"
	)
	
	updates = initBy(lambda self: OnRequestQueue())
	player = None

state = State()
	