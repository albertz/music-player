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

	@property
	def metadata(self):
		if hasattr(self, "_metadata"): return self._metadata
		import State
		player = State.state.player
		if not player: return {}
		if player.curSong is not self: return {}
		m = player.curSongMetadata or {}
		m = dict([(key.lower(),value) for (key,value) in m.items()])
		m["duration"] = player.curSongLen
		self._metadata = m
		return m
		
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
