# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import utils, math
from utils import UserAttrib, initBy, Event, formatTime
import Traits
import songdb

class Search:
	Keys = ("artist", "title", "duration", "rating")
	def __init__(self):
		self._searchText = ""
		self._searchResults = []
		import threading
		self._lock = threading.RLock()
		self._runningSearches = set()
	
	def _startSearch(self, txt):
		def search():
			try:
				import thread
				with self._lock:
					self._runningSearches.add(thread.get_ident())
					if self._searchText != txt: return
				res = songdb.search(txt)
				with self._lock:
					if self._searchText == txt:
						self._searchResults = res
						self.searchResults_updateEvent.push()
				with self._lock:
					self._runningSearches.discard(thread.get_ident())
			except utils.AsyncInterrupt:
				pass
		with self._lock:
			self._searchText = txt
			for tid in self._runningSearches:
				utils.raiseExceptionInThread(tid)
			self._runningSearches.clear()
			utils.daemonThreadCall(search, name="Song DB search")

	@UserAttrib(type=Traits.EditableText, searchLook=True)
	def searchText(self, updateText=None):
		with self._lock:
			if updateText is not None and self._searchText != updateText:
				self._startSearch(updateText)
		return self._searchText
	
	@UserAttrib(type=Traits.Table(keys=Keys,
		format_duration=lambda d: formatTime(d) if d > 0 else "",
		format_rating=lambda r: "★" * int(round(r * 5))))
	@property
	def searchResults(self):
		return list(self._searchResults)

	@searchResults.setUpdateEvent
	@initBy
	def searchResults_updateEvent(self): return Event()
	
search = Search()
