class Song:
	def __init__(self, fn):
		self.url = fn
		self.f = open(fn)
	
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
	
	def __repr__(self):
		return "Song(%r)" % self.url

	def __str__(self):
		import os
		return "Song(%s)" % os.path.basename(self.url)

	@property
	def metadata(self):
		if hasattr(self, "_metadata"): return self._metadata
		import State
		player = State.state.player
		if not player: return {}
		if player.curSong is not self: return {}
		if player.curSongMetadata:
			self._fileMetadata = player.curSongMetadata
			m = dict([(key.lower(),value) for (key,value) in self._fileMetadata.items()])
		else:
			m = {}
		self._metadata = m
		m["duration"] = player.curSongLen
		if hasattr(self, "rating"): m["rating"] = self.rating
		self.fixupMetadata()
		self.guessMetadata()
		return m

	def fixupMetadata(self):
		m = self.metadata
		def fixString(key):
			if key in m:
				m[key] = m[key].strip()
			else:
				return
			if m[key] in ["", "Unknown", "Unknown " + key]:
				del m[key]
		fixString("artist")
		fixString("title")

	_guessRegexps = [
		"^(?P<artist>.+?)\s-\s(?P<title>.+)$",
		"^(?P<artist>.+?)-(?P<title>.+)$",
	]

	def guessMetadata(self):
		""" guesses metadata from filename. the current metadata is expected to be fixed (fixupMetadata). """
		metadata = self.metadata
		if "artist" in metadata and "title" in metadata: return # that's enough for most usage, no need to guess
		import re, os
		basename = os.path.basename(self.url)
		basename = os.path.splitext(basename)[0]
		for r in self._guessRegexps:
			match = re.match(r, basename)
			if not match: continue
			match = match.groupdict()
			metadata["artist"] = match["artist"]
			metadata["title"] = match["title"]
			return

	@property
	def artist(self):
		return self.metadata.get("artist", "Unknown artist").strip()
		
	@property
	def track(self):
		return self.metadata.get("title", "Unknown title").strip()
		
	@property
	def duration(self):
		return self.metadata.get("duration", -1)
	
	@property
	def fileext(self):
		import os
		return os.path.splitext(self.url)[1][1:]

	@property
	def userString(self):
		artist = self.metadata.get("artist", "").strip()
		title = self.metadata.get("title", "").strip()
		if artist and title: return artist + " - " + title
		import os
		return os.path.basename(self.url)
