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
	def __init__(self, list=[], previous=None, index=0):
		self.index = index
		self.list = deque(list)
		self.previous = None
	def append(self, song):
		if not song: return
		self.list.append(song)
		if len(self.list) >= self.Limit:			
			newList = PersistentObject(RecentlyplayedList, "recentlyplayed-%i.dat" % self.index, persistentRepr=True)
			newList.index = self.index
			newList.list = self.list
			newList.previous = self.previous
			newList.save()			
			self.index += 1
			self.previous = newList
			self.list = deque()
	def __repr__(self):
		return "RecentlyplayedList(list=%s, previous=%s)" % (
			betterRepr(self.list),
			betterRepr(self.previous))

def loadRecentlyplayedList(state):
	return PersistentObject(RecentlyplayedList, "recentlyplayed.dat")

class PlayerEventCallbacks:
	onSongChange = None
	onSongFinished = None
	onPlayingStateChange = None

def loadPlayer(state):
	import ffmpeg
	player = ffmpeg.createPlayer()
	for e in [m for m in dir(PlayerEventCallbacks) if not m.startswith("_")]:
		cb = EventCallback(targetQueue=state.updates, name=e)
		setattr(PlayerEventCallbacks, e, cb)
		setattr(player, e, cb)
	player.queue = state.queue
	return player

def playerMain():
	state.player.playing = True
	for ev,args,kwargs in state.updates.read():
		if ev is PlayerEventCallbacks.onSongChange:
			state.curSong = kwargs["newSong"]
			state.curSong.save()
			state.recentlyPlayedList.append(kwargs["oldSong"])
			state.recentlyPlayedList.save()
		pass # onPlayingStateChange
		
class State(object):
	queue = initBy(loadQueue)
	recentlyPlayedList = initBy(loadRecentlyplayedList)
	curSong = initBy(lambda self: PersistentObject(Song, "cursong.dat"))
	
	playState = oneOf(
		"playing",
		"paused"
	)
	
	updates = initBy(lambda self: OnRequestQueue())
	player = initBy(loadPlayer)

state = State()
