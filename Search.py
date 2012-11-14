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
	_searchText = ""
	_searchResults = []
	
	@UserAttrib(type=Traits.EditableText, searchLook=True)
	def searchText(self, updateText=None):
		if updateText is not None and self._searchText != updateText:
			self._searchText = updateText
			self._searchResults = songdb.search(updateText)
			self.searchResults_updateEvent.push()
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
