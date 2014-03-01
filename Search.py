# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import utils, math
from utils import UserAttrib, initBy, Event, formatTime
import Traits
import songdb
import gui

class Search:
	Keys = ("artist", "title", "duration", "rating")
	def __init__(self):
		self._searchText = ""
		self._searchResults = []
		import threading
		self._lock = threading.RLock()
	
	def _startSearch(self, txt):
		def search():
			with self._lock:
				if self._searchText != txt: return
			res = songdb.search(txt)
			with self._lock:
				if self._searchText == txt:
					self._searchResults = res
					self.__class__.searchResults.updateEvent(self).push()
		with self._lock:
			self._searchText = txt
			utils.daemonThreadCall(search, name="Song DB search")

	@UserAttrib(type=Traits.EditableText, searchLook=True)
	def searchText(self, updateText=None):
		with self._lock:
			if updateText is not None and self._searchText != updateText:
				self._startSearch(updateText)
		return self._searchText
	
	@UserAttrib(type=Traits.Table(keys=Keys,
		format_duration=lambda d: formatTime(d) if d > 0 else "",
		format_rating=lambda r: "★" * int(round(r * 5))),
		variableHeight=True,
		addUpdateEvent=True)
	@property
	def searchResults(self):
		with self._lock:
			return list(self._searchResults)

search = Search()

gui.registerRootObj(obj=search, name="Search", priority=-1, keyShortcut='2')
