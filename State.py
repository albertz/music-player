# -*- coding: utf-8 -*-

from utils import *
from Song import Song

def loadQueue(state):
	print "load queue"
	
	def songs():
		if state.curSong:
			# We just started the player and we have a current song from persistent storage.
			# Yield it now so that we begin playing with this song.
			# Yield the Song object itself, though, not the ObjectProxy. The ObjectProxy
			# would result in very strange behavior later for onSongChange events.
			song = state.curSong.__get__(None)
			song.openFile()
			yield song
		import queue
		while True:
			song = queue.getNextSong()
			song.openFile()
			yield song

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
	def getLastN(self, n):
		#return list(self.list)[-n:] # not using this for now as a bit too heavy. I timeit'd it. this is 14 times slower for n=10, len(l)=10000
		l = self.list # better for multithreading to keep the ref
		return [l[-i] for i in range(1,min(len(l),n)+1)]
	def __repr__(self):
		return "RecentlyplayedList(list=%s, previous=%s, index=%i)" % (
			betterRepr(self.list),
			betterRepr(self.previous),
			self.index)



class Actions:
	def play(self): state.player.playing = True
	def pause(self): state.player.playing = False
	def next(self): state.player.nextSong()
	def forward10s(self): state.player.seekRel(10)

actions = Actions()

from player import loadPlayer, PlayerEventCallbacks
import Traits

class State(object):
	def playPauseUpdate(self, attrib, *args):
		if self.player.playing:
			attrib.name = "❚❚"
		else:
			attrib.name = "▶"

	@UserAttrib(type=Traits.Action, name="▶", updateHandler=playPauseUpdate)
	def playPause(self):
		self.player.playing = not self.player.playing

	@UserAttrib(type=Traits.Action, name="▶▶|", alignRight=True)
	def nextSong(self):
		self.player.nextSong()

	@UserAttrib(type=Traits.OneLineText, updateHandler=lambda *args:None, alignRight=True)
	@property
	def curSongStr(self):
		try: return self.player.curSong.userString
		except: return "???"

	@UserAttrib(type=Traits.List)
	@initBy
	def recentlyPlayedList(self): return PersistentObject(RecentlyplayedList, "recentlyplayed.dat")

	@UserAttrib(type=Traits.Object, updateHandler=lambda *args:None)
	@initBy
	def curSong(self): return PersistentObject(Song, "cursong.dat")

	@UserAttrib(type=Traits.List)
	@initBy
	def queue(self): return loadQueue(self)

	@initBy
	def updates(self): return OnRequestQueue()

	@initBy
	def player(self): return loadPlayer(self)

	def quit(self):
		""" This works in all threads except the main thread. It will quit the whole app.
		For more information about why we do it this way, read the comment in main.py.
		"""
		import sys, os, signal
		os.kill(0, signal.SIGINT)
		sys.exit()

# Only init new state if it is new, not at module reload.
try:
	state
except NameError:
	state = State()

try:
	modules
except NameError:
	modules = []

def getModule(modname):
	for m in modules:
		if m.name == modname: return m
	return None

for modname in [
	"player",
	"queue",
	"tracker",
	"mediakeys",
	"gui",
	"stdinconsole",
	"notifications",
]:
	if not getModule(modname):
		modules.append(Module(modname))

for m in modules:
	print m

def reloadModules():
	# reload some custom random Python modules
	import utils
	reload(utils)
	import Song, State
	reload(Song)
	reload(State)
	# reload all our modules
	for m in modules:
		m.reload()
