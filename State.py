from utils import *
from Song import Song
import appinfo

player = None

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
			yield Song(f, state._main["player"])
			
	return songs()
	
def loadRecentlyplayedList(state):
	#class RecentlyplayedList:
	#	def __i
	return None

class State:
	queue = initBy(loadQueue)
	recentlyPlayedList = initBy(loadRecentlyplayedList)
	
	playState = oneOf(
		"playing",
		"paused"
	)

	def __init__(self, main):
		self._main = main
		