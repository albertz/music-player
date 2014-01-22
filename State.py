# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

from utils import *
import Traits
from Song import Song

from collections import deque
from threading import RLock

class RecentlyplayedList(object):
	GuiLimit = 5
	Limit = 500
	def __init__(self, list=[], previous=None, index=0):
		self.lock = RLock()
		self.index = index
		self.list = deque(list)
		if previous:
			if not getattr(previous, "_isPersistentObject", False):
				# This was some bug from earlier... Fix it now.
				print "Warning: RecentlyplayedList.previous is not a PersistentObject"
				previous = PersistentObject(RecentlyplayedList, "recentlyplayed-%i.dat" % previous.index, persistentRepr=True)
			elif not previous._persistentRepr:
				# This was some bug from earlier... Fix it now.
				print "Warning: RecentlyplayedList.previous not persistentRepr"
				previous = PersistentObject(RecentlyplayedList, previous._filename, persistentRepr=True)
			assert previous._isPersistentObject
			assert previous._persistentRepr
		self.previous = previous
	def append(self, song):
		if not song: return
		with self.lock:
			guiOldLen = len(self)
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
			self.onInsert.push(guiOldLen, song)
			if guiOldLen == self.GuiLimit: self.onRemove.push(0)
	def getLastN(self, n):
		with self.lock:
			#return list(self.list)[-n:] # not using this for now as a bit too heavy. I timeit'd it. this is 14 times slower for n=10, len(l)=10000
			l = self.list
			if n <= len(l):
				return [l[-i] for i in range(1,n+1)]
			else:
				last = [l[-i] for i in range(1,len(l)+1)]
				if self.previous:
					last += self.previous.getLastN(n - len(l))
				return last
	def __repr__(self):
		return "RecentlyplayedList(list=%s, previous=%s, index=%i)" % (
			betterRepr(list(self.list)),
			betterRepr(self.previous),
			self.index)
	
	@initBy
	def onInsert(self): return Event() # (index, value)
	@initBy
	def onRemove(self): return Event() # (index)
	@initBy
	def onClear(self): return Event() # ()

	def __getitem__(self, index):
		with self.lock:
			return self.getLastN(self.GuiLimit)[-index - 1]
	def __len__(self):
		c = len(self.list)
		if c >= self.GuiLimit: return self.GuiLimit
		if self.previous:
			c += len(self.previous)
		return min(c, self.GuiLimit)



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

	@UserAttrib(type=Traits.SongDisplay, variableWidth=True)
	def curSongDisplay(self): pass

	@initBy
	def _volume(self): return PersistentObject(float, "volume.dat", defaultArgs=(0.9,))

	@UserAttrib(type=Traits.Real(min=0, max=2), alignRight=True, height=80, width=25)
	@property
	def volume(self):
		return self._volume
	
	@volume.callDeco.setter
	def volume(self, updateValue):
		self._volume = updateValue
		self._volume.save()
		self.player.volume = updateValue

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
			sys.stdin.close() # so that the terminal closes, if it is used
			import gui
			gui.quit() # might do some additional stuff
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
	"tracker_lastfm",
	"mediakeys",
	"gui",
	"stdinconsole",
	"socketcontrol",
	"mpdBackend",
	"notifications",
	"preloader",
	"songdb",
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
