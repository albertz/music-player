from utils import *
from Song import Song

def loadQueue(state):
	print "load queue"
	
	def songs():
		if state.curSong:
			# We just started the player and we have a current song from persistent storage.
			# Yield it now so that we begin playing with this song.
			yield state.curSong
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
	Limit = 500
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
		return "RecentlyplayedList(list=%s, previous=%s, index=%i)" % (
			betterRepr(self.list),
			betterRepr(self.previous),
			self.index)

def loadRecentlyplayedList(state):
	return PersistentObject(RecentlyplayedList, "recentlyplayed.dat")


class Actions:
	def play(self): state.player.playing = True
	def pause(self): state.player.playing = False
	def next(self): state.player.nextSong()
	def forward10s(self): state.player.seekRel(10)

actions = Actions()

from player import loadPlayer

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

	def quit(self):
		""" This works in all threads except the main thread. It will quit the whole app.
		For more information about why we do it this way, read the comment in main.py.
		"""
		import sys, os, signal
		os.kill(0, signal.SIGINT)
		sys.exit()

state = State()
