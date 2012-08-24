class Song:
	def __init__(self, fn):
		self.url = fn
		self.f = open(fn)
	def readPacket(self, bufSize):
		s = self.f.read(bufSize)
		return s
	def seekRaw(self, offset, whence):
		r = self.f.seek(offset, whence)
		return self.f.tell()
	def __repr__(self):
		return "<Song %r>" % self.url
