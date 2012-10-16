# -*- coding: utf-8 -*-

from utils import *
import Traits
from Song import Song

from collections import deque
from threading import RLock

class RecentlyplayedList:
	GuiLimit = 5
	Limit = 500
	def __init__(self, list=[], previous=None, index=0):
		self.lock = RLock()
		self.index = index
		self.list = deque(list)
		self.previous = None
	def append(self, song):
		if not song: return
		with self.lock:
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
				self.onClear()
			else:
				self.onInsert(min(len(self.list), self.GuiLimit), song)
				if len(self.list) > self.GuiLimit: self.onRemove(0)
	def getLastN(self, n):
		#return list(self.list)[-n:] # not using this for now as a bit too heavy. I timeit'd it. this is 14 times slower for n=10, len(l)=10000
		l = self.list # better for multithreading to keep the ref
		return [l[-i] for i in range(1,min(len(l),n)+1)]
	def __repr__(self):
		return "RecentlyplayedList(list=%s, previous=%s, index=%i)" % (
			betterRepr(list(self.list)),
			betterRepr(self.previous),
			self.index)
	
	def onInsert(self, index, value): pass
	def onRemove(self, index): pass
	def onClear(self): pass
	def __getitem__(self, index):
		with self.lock:
			if index >= 0 and len(self.list) > self.GuiLimit:
				return self.list[len(self.list) - self.GuiLimit + index]
			else:
				return self.list[index]
	def __len__(self):
		return min(len(self.list), self.GuiLimit)


class Actions:
	def play(self): state.player.playing = True
	def pause(self): state.player.playing = False
	def next(self): state.player.nextSong()
	def forward10s(self): state.player.seekRel(10)

actions = Actions()


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

	@UserAttrib(type=Traits.OneLineText, alignRight=True, variableWidth=True, withBorder=True)
	@property
	def curSongStr(self):
		if not self.player.curSong: return ""
		try: return self.player.curSong.userString
		except: return "???"

	@UserAttrib(type=Traits.OneLineText, alignRight=True, autosizeWidth=True, withBorder=True)
	@property
	def curSongPos(self):
		if not self.player.curSong: return ""
		try: return formatTime(self.player.curSongPos) + " / " + formatTime(self.player.curSong.duration)
		except: return "???"

	@UserAttrib(type=Traits.SongDisplay)
	def curSongDisplay(self): pass

	@UserAttrib(type=Traits.List, lowlight=True, autoScrolldown=True)
	@initBy
	def recentlyPlayedList(self): return PersistentObject(RecentlyplayedList, "recentlyplayed.dat")

	@UserAttrib(type=Traits.Object, spaceY=0, highlight=True)
	@initBy
	def curSong(self): return PersistentObject(Song, "cursong.dat")

	@UserAttrib(type=Traits.Object, spaceY=0)
	@initBy
	def queue(self):
		import queue
		return queue.queue

	@initBy
	def updates(self): return OnRequestQueue()

	@initBy
	def player(self):
		from player import loadPlayer
		return loadPlayer(self)

	def quit(self):
		def doQuit():
			""" This works in all threads except the main thread. It will quit the whole app.
			For more information about why we do it this way, read the comment in main.py.
			"""
			import sys, os, signal
			os.kill(0, signal.SIGINT)
		import thread
		thread.start_new_thread(doQuit, ())

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
	"preloader",
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
