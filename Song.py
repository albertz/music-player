# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import Traits
from utils import UserAttrib, safe_property
import utils

class Song(object):
	"""
	The Song object. It represents a Song. It is also compatible to the ffmpeg.player.
	It also stores information about the song.
	Songs are considered as equal if they are they have the same url.
	Note that we have *some* additional state, thus equal Song objects
	are different internally:
	- self.f: the open file handle (and its state)
	- self.skipped: the song was skipped on last play
	
	In the database (songdb), songs are a bit more generic. Songs with the
	same fingerprint (AcoustID right now) are considered the same. They each
	have a dict about each file/url.
	"""
	
	# This should be the list of all attribs in __repr__.
	# This is *not* the list of all further attribs (like bmpThumbnail).
	url = None
	skipped = False

	def __init__(self, *args, **kwargs): # we must support an empty init for PersistentObject
		self.f = None
		self._fileMetadata = None
		self._metadata = None
		self._useDb = True
		for key,value in kwargs.items():
			setattr(self, key, value)
		if len(args) == 1: # guess this is the url
			assert "url" not in kwargs
			self.url = args[0]
		if self.url:
			self.url = utils.convertToUnicode(self.url)

	def __nonzero__(self): # this is mostly for noninited Song objects
		return bool(self.url)
	def __eq__(self, other):
		return hasattr(other, "url") and self.url == other.url
	def __ne__(self, other):
		return not self == other
	def openFile(self):
		if not self.f:
			self.f = open(self.url)

	# { ffmpeg player interface
	def readPacket(self, bufSize):
		s = self.f.read(bufSize)
		return s
	def seekRaw(self, offset, whence):
		r = self.f.seek(offset, whence)
		return self.f.tell()
	# ffmpeg player interface end }
	
	def close(self):
		self.f = None

	# returns list of all root attrib names
	@safe_property
	@property
	def rootAttribNames(self):
		# TODO: maybe cache this?
		l = []
		import types
		for attrName in dir(self.__class__):
			if attrName.startswith("_"): continue
			attr = getattr(self.__class__, attrName)
			if isinstance(attr, types.UnboundMethodType): continue
			if isinstance(attr, property): continue
			l += [attrName]
		return l

	# returns custom/changed root attrib dict
	@safe_property
	@property
	def rootAttribDict(self):
		d = {}
		attribs = self.rootAttribNames
		for attr in self.__dict__:
			if attr in attribs:
				d[attr] = getattr(self, attr)
		return d

	def __repr__(self):
		# This has changed back and forth.
		# __repr__ is used by PersistentObject. Thus, we want all information here
		# which are important for later usage.
		return "Song(%s)" % (", ".join(["%s=%r" % (key,value) for (key,value) in self.rootAttribDict.items()]))

	def __str__(self):
		if not self.url: return "Song()"
		import os
		return "Song(%s)" % os.path.basename(self.url)

	@safe_property
	@property
	def metadata(self):
		if self._metadata is not None: return self._metadata
		import State
		player = State.state.player
		if self._fileMetadata is None:
			if player and player.curSong is self:
				self._fileMetadata = player.curSongMetadata or {}
			else:
				# try to read the metadata manually
				try:
					# make a new songObj. this prevents any multithreading issues
					songObj = Song(url=self.url, _useDb=False)
					songObj.openFile()
					import ffmpeg
					self._fileMetadata = ffmpeg.getMetadata(songObj) or {}
				except Exception: pass # couldn't open or so
		if self._fileMetadata is not None:
			m = dict([(key.lower(),value) for (key,value) in self._fileMetadata.items()])
			self._metadata = m # only save attrib if this is from player. otherwise we might get later some better results
		else:
			m = {}
		self.fixupMetadata(m)
		self.guessMetadata(m)
		self.makeMetadataUnicode(m)
		return m

	def fixupMetadata(self, metadata=None):
		if metadata is None: metadata = self.metadata
		def fixString(key):
			if key in metadata:
				metadata[key] = metadata[key].strip()
			else:
				return
			if metadata[key] in ["", "Unknown", "Unknown " + key]:
				del metadata[key]
		fixString("artist")
		fixString("title")
		
	def makeMetadataUnicode(self, metadata=None):
		import utils
		if metadata is None: metadata = self.metadata
		for key, value in metadata.items():
			if not isinstance(value, str): continue
			metadata[key] = utils.convertToUnicode(value)
	
	_guessRegexps = [
		"^(.*/)*(?P<artist>.+?)/(?P<album>.+?)/(?P<track>\d+)(\s*-)?\s*(?P<title>.+)$",
		"^(.*/)*(?P<artist>.+?)\s-\s(?P<title>.+)$",
		"^(.*/)*(?P<artist>.+?)-(?P<title>.+)$",
		"^(.*/)*(?P<artist>.+?)/(?P<album>.+?)/(?P<title>.+)$",
	]

	def guessMetadata(self, metadata=None):
		""" guesses metadata from filename. the current metadata is expected to be fixed (fixupMetadata). """
		if self.url is None: return # nothing we can do here
		if metadata is None: metadata = self.metadata
		if "artist" in metadata and "title" in metadata: return # that's enough for most usage, no need to guess
		import re, os
		fn = os.path.splitext(self.url)[0]
		# For now, just take the first matching.
		# Later improvement might be:
		#  - Collect all matching.
		#  - Calculate some likelihood for each (e.g. guess that number-only strings are probably not artist names, etc.)
		for r in self._guessRegexps:
			match = re.match(r, fn)
			if not match: continue
			match = match.groupdict()
			for key in match:
				if match[key] is not None:
					metadata[key] = match[key]
			#print "guessed metadata:", metadata, "from", fn
			return

	@property
	def fileext(self):
		if self.url is None: return ""
		import os
		return os.path.splitext(self.url)[1][1:]

	@safe_property
	@property
	def userString(self):
		artist = self.metadata.get("artist", "").strip()
		title = self.metadata.get("title", "").strip()
		if artist and title: return artist + " - " + title
		if self.url is None: return "No song"
		import os
		return os.path.basename(self.url)			

	@UserAttrib(type=Traits.OneLineText, variableWidth=True)
	@safe_property
	@property
	def userLongString(self):
		import utils
		s = self.userString
		duration = getattr(self, "duration", -1)
		if duration >= 0:
			s += ", " + utils.formatTime(duration)
		try:
			import os
			size = os.stat(self.url).st_size
		except Exception:
			size = None
		s += ", " + self.fileext
		if size and duration > 0:
			s += ", %.3g kbit/s" % (size * 8 / 1024. / duration)
		if size:
			s += ", " + utils.formatFilesize(size)
		return s
	
	@safe_property
	@property
	def userLongDescription(self):
		data = dict(self.metadata)
		mainKeys = ["artist","title"]
		for key in mainKeys:
			data[key] = data.get(key, "").strip()
		# TODO ...
		data = sorted()
	
	@safe_property
	@property
	def id(self):
		if getattr(self, "_id", None): return self._id
		if not self._useDb: return None
		
		# avoid recursive calls. those might happen because
		# calcNewSongId or getSongId will again access Song attribs.
		if getattr(self, "_recursive_id_call", False): return None
		self._recursive_id_call = True
		
		try:
			import songdb
			self._id = songdb.getSongId(self)
			if not self._id:
				self._id = songdb.calcNewSongId(self)
		except Exception:
			print "errors while getting song id"
			import sys
			sys.excepthook(*sys.exc_info())
			
		self._recursive_id_call = False
		return self._id
	
	@id.setter
	def id(self, value):
		self._id = value
	
	# These _calc_<attrib> functions specify how to calculate
	# song.<attrib>. In the DB, this is all file-specific, i.e.
	# song.files[song.url].<attrib>.
	# The _calc_<attrib> functions return a dict with the attribs we got.
	# This is expected to be with accuracy=1. It might also be stored
	# in the DB, where everything is expected to have accuracy=1.
	# The _estimate_<attrib> functions are expected to be fast.
	# They return (value,accuracy). They are optional.
	
	def _calc_fingerprint_AcoustId(self):
		song = Song(url = self.url, _useDb = False)
		song.openFile()
		song.gain = 0 # just use original
		import ffmpeg
		duration, fingerprint = ffmpeg.calcAcoustIdFingerprint(song)
		# fingerprint is URL-safe base64 with missing padding
		fingerprint += "==="
		import base64
		fingerprint = base64.urlsafe_b64decode(fingerprint)
		return {"duration": duration, "fingerprint_AcoustId": fingerprint}
	
	def _calc_bmpThumbnail(self):
		song = Song(url = self.url, _useDb = False)
		song.gain = self.gain # useful for the adopted BMP
		song.openFile() # this is another process, so safe
		# We have song.gain which mostly lowers the volume. So increase here for nicer display.
		import ffmpeg
		duration, bmpData = ffmpeg.calcBitmapThumbnail(song, 600, 81, volume = 1.5)
		return {"duration": duration, "bmpThumbnail": bmpData}
	
	def _calc_gain(self):
		song = Song(url = self.url, _useDb = False)
		song.openFile() # this is another process, so safe
		import ffmpeg
		duration, gain = ffmpeg.calcReplayGain(song)
		return {"duration": duration, "gain": gain}

	_calc_duration = _calc_gain # if that is needed
	
	def _estimate_duration(self):
		# this metatag info might be inaccurate
		d = self.metadata.get("duration", None)
		if d is None: return None, 0
		if d <= 0: return None, 0
		assert isinstance(d, float)
		return d, 0.8

	def _calc_sha1(self):
		import songdb
		return {"sha1": songdb.hashFile(self.url)}

	def _estimate_artist(self):
		s = self.metadata.get("artist", "").strip()
		#if not s: return None, 0
		# We don't know wether correct or not. But we want to have it
		# saved in the DB, so use accuracy=1.
		return s, 1
	
	def _estimate_album(self):
		s = self.metadata.get("album", "").strip()
		# Take empty string as valid. There might be songs without an album.
		return s, 1

	def _estimate_title(self):
		s = self.metadata.get("title", "").strip()
		#if not s: return None, 0
		# We don't know wether correct or not. But we want to have it
		# saved in the DB, so use accuracy=1.
		return s, 1

	# dict from tag to value [0,1] (weighted tagmap, tag fuzzy set)
	def _estimate_tags(self):
		import re
		taglist = re.split("\s*(?:,|/|;)?\s*", self.metadata.get("genre", ""))
		taglist = filter(None, taglist)
		#if not taglist: return None, 0
		# We want to have it saved in the DB, so use accuracy=1.
		return dict([(tag,1.0) for tag in taglist]), 1

	# returns None or realnum in [0,1]
	def _estimate_rating(self):
		# Check if we have iTunes ratings.
		# If we have, 
		import itunes
		itunes_rating = itunes.ratings.get(self.url, None)
		if itunes_rating is not None:
			# It is not yet in our DB, otherwise we would not have called
			# this func (see getFast() for reference).
			# Thus, return it as accuracy=1 to save it as initial value in our DB.
			return itunes_rating, 1
		# Return 0. This is a good estimation.
		return 0, 0.7

	def update(self, attr, updateFunc, default=None):
		"updateFunc is supposed to be oldValue->newValue."
		"E.g. you can increment by one or so. While updateFunc is executed, the DB is blocked."
		import songdb
		if getattr(self, "_useDb", False) and attr in songdb.Attribs:
			value = songdb.updateSongAttribValue(self, attr, updateFunc, default=default)
		else:
			# Note that we don't use getattr to get the old value for the updateFunc.
			# This is to avoid infinite recursion loops and also because
			# it doesn't exactly match the useDb-case where we don't use getattr
			# but the old value in the DB.
			value = updateFunc(default)
		# Note that locally stored attribs might get outdated.
		# Thus, in getFast(), those will not be returned for accuracy=1.
		object.__setattr__(self, attr, value)
		
	def __setattr__(self, attr, value):
		self.update(attr, lambda _: value)
		
	def calcAndSet(self, attrib):
		from utils import asyncCall
		res = asyncCall(
			func = getattr(self, "_calc_" + attrib),
			name = "calc Song(%s) %s" % (self.userString.encode("utf-8"), attrib))
		for attr,value in res.items():
			setattr(self, attr, value)
		value = getattr(self, attrib)
		return value

	LocalAttribAccuracy = 0.9
	
	def getFast(self, attrib, accuracy=1):
		# self.__getattr__ is wrapped and calls getFast().
		# Thus, access self.__dict__ directly.
		# First, check local self.__dict__ cache.
		if accuracy <= self.LocalAttribAccuracy and attrib in self.__dict__:
			return utils.fixValue(self.__dict__[attrib]), self.LocalAttribAccuracy
		# Now try the DB.
		import songdb
		if attrib in songdb.Attribs and self._useDb and self.id:
			try:
				value = songdb.getSongAttrib(self, attrib)
				value = utils.fixValue(value)
			except AttributeError: pass
			else:
				# Cache it locally.
				object.__setattr__(self, attrib, value)
				# We expect perfect accuracy if we have it in the DB.
				return value, 1
		# All has failed so far. Try the estimate function.
		estimateFunc = getattr(self, "_estimate_" + attrib, None)
		if estimateFunc:
			value, estAccuracy = estimateFunc()
			value = utils.fixValue(value)
			if estAccuracy == 1:
				# save locally and in DB
				setattr(self, attrib, value)
			if estAccuracy >= accuracy:
				return value, estAccuracy
		return None, 0
	
	def get(self, attrib, timeout=0, accuracy=1, callback=None, fastOnly=False):
		assert self
		if fastOnly:
			assert callback is None, "we aren't going to use callback as we are not doing the calculation"
		
		fastValue, fastAccuracy = self.getFast(attrib, accuracy)
		if fastAccuracy == 1 or fastOnly: return fastValue, fastAccuracy
		
		import threading
		lock = threading.Lock()
		afterJoinEvent = threading.Event()
		gotNewValueEvent = threading.Event()
		def doCalc():
			value = self.calcAndSet(attrib)
			with lock:
				if not afterJoinEvent.isSet():
					return
				if gotNewValueEvent.isSet():
					return
			if callback: callback(self, attrib, value)
		t = threading.Thread(target=doCalc, name = "Song(%s) attrib %s calc" % (self.userString.encode("utf-8"), attrib))
		t.daemon = True
		t.start()
		t.join(timeout=timeout)
		
		with lock:
			afterJoinEvent.set()
			fastValue, fastAccuracy = self.getFast(attrib, accuracy)
			if fastAccuracy == 1: gotNewValueEvent.set()

		return fastValue, fastAccuracy

	GetAttrAccuracy = 0.7
	
	def __getattr__(self, attrib):
		# This is only called when it is not found in self.__dict__ or the class.
		# First, filter some stuff which we will never have. We also need
		# that to avoid infinite loops in some simplified code.
		if attrib == "" or attrib.startswith("_"):
			raise AttributeError, "no attrib " + attrib
		if not self:
			raise AttributeError, "not initialized yet"
		try:
			value,accuracy = self.get(
				attrib,
				accuracy=self.GetAttrAccuracy,
				fastOnly=True)
		except AttributeError:
			# Catch that here, otherwise we might get strange behaviour
			sys.excepthook(*sys.exc_info())					
			value,accuracy = None, 0
		if accuracy < self.GetAttrAccuracy:
			raise AttributeError, "attrib " + attrib + " is not yet available"		
		return value
	

	NumStars = 5
	def _starHandler(self, starIndex, handleClick):
		starRating = float(starIndex) / self.NumStars
		limit = 0.5 / self.NumStars
		if handleClick:
			if abs(self.rating - starRating) < limit:
				self.rating = starRating - 1.0 / self.NumStars
			else:
				self.rating = starRating
		if self.rating - starRating < -limit:
			return "☆"
		else:
			return "★"

	@UserAttrib(type=Traits.ClickableLabel, autosizeWidth=True, alignRight=True, spaceX=0)
	def locateFile(self, handleClick=False):
		if handleClick:
			import gui
			gui.locateFile(self.url)
		return "⬆"
		
	@UserAttrib(type=Traits.ClickableLabel, autosizeWidth=True, alignRight=True, spaceX=0)
	def star1(self, handleClick=False): return self._starHandler(1, handleClick)
	@UserAttrib(type=Traits.ClickableLabel, autosizeWidth=True, alignRight=True, spaceX=0)
	def star2(self, handleClick=False): return self._starHandler(2, handleClick)
	@UserAttrib(type=Traits.ClickableLabel, autosizeWidth=True, alignRight=True, spaceX=0)
	def star3(self, handleClick=False): return self._starHandler(3, handleClick)
	@UserAttrib(type=Traits.ClickableLabel, autosizeWidth=True, alignRight=True, spaceX=0)
	def star4(self, handleClick=False): return self._starHandler(4, handleClick)
	@UserAttrib(type=Traits.ClickableLabel, autosizeWidth=True, alignRight=True, spaceX=0)
	def star5(self, handleClick=False): return self._starHandler(5, handleClick)
		
def test():
	# These are testing guessMetadata.
	s = Song("/yyy/xxx/Tool/Lateralus/12 Triad.flac")
	assert s.metadata["artist"] == "Tool"
	assert s.metadata["album"] == "Lateralus"
	assert s.metadata["title"] == "Triad"
	assert s.metadata["track"] == "12"
	s = Song("/yyy/xxx/Tool/Lateralus/Triad.flac")
	assert s.metadata["artist"] == "Tool"
	assert s.metadata["album"] == "Lateralus"
	assert s.metadata["title"] == "Triad"
	s = Song("/zzz/yyy/xxx/abc - foo - bar")
	assert s.metadata["artist"] == "abc"
	assert s.metadata["title"] == "foo - bar"

if __name__ == "__main__":
	print "*** testing"
	test()
