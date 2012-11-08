# -*- coding: utf-8 -*-

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
		format_duration=formatTime, format_rating=lambda r: "★" * int(round(r * 5))))
	@property
	def searchResults(self):
		return list(self._searchResults)

	@searchResults.setUpdateEvent
	@initBy
	def searchResults_updateEvent(self): return Event()
	
search = Search()
