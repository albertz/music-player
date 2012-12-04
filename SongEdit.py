# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

from utils import UserAttrib, Event, initBy
import Traits

# Note: I'm not too happy with all the complicated update handling here...
# In general, the design is ok. But it needs some more specification
# and then some drastic simplification. Most of it should be one-liners.

class SongEdit:
	@initBy
	def _updateEvent(self): return Event()
	
	def __init__(self, ctx=None):
		if not ctx:
			import gui
			ctx = gui.ctx()
			assert ctx, "no gui context"
		self.ctx = ctx
		self._updateHandler = lambda: self._updateEvent.push()
		ctx.curSelectedSong_updateEvent.register(self._updateHandler)
		
	@UserAttrib(type=Traits.Object)
	@property
	def song(self):
		return self.ctx.curSelectedSong	

	@UserAttrib(type=Traits.EditableText)
	def artist(self, updateText=None):
		if self.song:
			if updateText:
				self.song.artist = updateText
			return self.song.artist
		return ""
	
	@UserAttrib(type=Traits.EditableText)
	def title(self, updateText=None):
		if self.song:
			if updateText:
				self.song.title = updateText
			return self.song.title
		return ""

	@staticmethod
	def _convertTagsToText(tags):
		def txtForTag(tag):
			value = tags[tag]
			if value >= 1: return tag
			return tag + ":" + str(value) 
		return " ".join(map(txtForTag, sorted(tags.keys())))

	@staticmethod
	def _convertTextToTags(txt):
		pass
	
	# todo...
	#@UserAttrib(type=Traits.EditableText)
	def tags(self, updateText=None):
		if self.song:
			return self._convertTagsToText(self.song.tags)
		return ""

	@UserAttrib(type=Traits.Table(keys=("key", "value")), variableHeight=True)
	@property
	def metadata(self):
		d = dict(self.song.metadata)
		for key in ("artist","title","url","rating","tags"):
			try: d[key] = unicode(getattr(self.song, key))
			except AttributeError: pass			
		l = []
		for key,value in d.items():
			l += [{"key": key, "value": value}]
		return l
	@metadata.setUpdateEvent
	@property
	def metadata_updateEvent(self): return self.song._updateEvent

	def _queryAcoustId(self):
		duration = self.song.duration
		fingerprint = self.song.fingerprint_AcoustId
		
		import base64
		fingerprint = base64.urlsafe_b64encode(fingerprint)
		
		api_url = "http://api.acoustid.org/v2/lookup"
		# "8XaBELgH" is the one from the web example from AcoustID.
		# "cSpUJKpD" is from the example from pyacoustid
		# get an own one here: http://acoustid.org/api-key
		client_api_key = "cSpUJKpD"
		
		params = {
			'format': 'json',
			'client': client_api_key,
			'duration': int(duration),
			'fingerprint': fingerprint,
			'meta': 'recordings recordingids releasegroups releases tracks compress',
		}
		
		import urllib
		body = urllib.urlencode(params)
		
		import urllib2
		req = urllib2.Request(api_url, body)
		
		import contextlib
		with contextlib.closing(urllib2.urlopen(req)) as f:
			data = f.read()
			headers = f.info()
		
		import json
		data = json.loads(data)
		return data

	def queryAcoustIdResults_selectionChangeHandler(self, selection):
		self._queryAcoustId_selection = selection
		
	@UserAttrib(type=Traits.Table(keys=("artist", "title", "album", "track", "score")),
		selectionChangeHandler=queryAcoustIdResults_selectionChangeHandler)
	@property
	def queryAcoustIdResults(self):
		if getattr(self, "_queryAcoustIdResults_songId", "") != getattr(self.song, "id", ""):
			return []
		return list(getattr(self, "_queryAcoustIdResults", []))
	@queryAcoustIdResults.setUpdateEvent
	@initBy
	def queryAcoustIdResults_updateEvent(self): return Event()
				
	@UserAttrib(type=Traits.Action, variableWidth=False)
	def queryAcoustId(self):
		data = self._queryAcoustId()
		
		self._queryAcoustIdResults_songId = self.song.id
		self._queryAcoustIdResults = []
		for result in data["results"]:
			for recording in result["recordings"]:
				for resGroup in recording["releasegroups"]:
					artist = resGroup["artists"][0]
					release = resGroup["releases"][0]
					medium = release["mediums"][0]
					track = medium["tracks"][0]
					if artist["name"] == "Various Artists":
						artist = track["artists"][0]
					entry = {
						"id": result["id"],
						"score": result["score"],
						"recording-id": recording["id"],
						"releasegroup-id": resGroup["id"],
						"artist-id": artist["id"],
						"artist": artist["name"],
						"title": track["title"],
						"album": resGroup["title"],
						"track": "%i/%i" % (track["position"], medium["track_count"])
					}
					self._queryAcoustIdResults += [entry]
		self.queryAcoustIdResults_updateEvent.push()
		
	@UserAttrib(type=Traits.Action, variableWidth=False, alignRight=True)
	def apply(self):
		if getattr(self, "_queryAcoustIdResults_songId", "") != getattr(self.song, "id", ""):
			return
		sel = getattr(self, "_queryAcoustId_selection", [])
		if not sel: return
		sel = sel[0]
		for key in ("artist","title","album","track"):
			setattr(self.song, key, sel[key])
		self._updateEvent.push() # the song is updating itself - but the edit fields aren't atm...

