import ffmpeg

class Song:
	def __init__(self, fn):
		self.f = open(fn)
		
	def readPacket(self, bufSize):
		s = self.f.read(bufSize)
		print "readPacket", self, bufSize, len(s)
		return s
		
def songs():
	while True:
		fn = "/Users/az/Music/Electronic/One Day_Reckoning Song (Wankelmut Remix) - Asaf Avidan & the Mojos.mp3"
		#fn = "/Users/az/Music/Electronic/Von Paul Kalkbrenner - Aaron.mp3"
		yield Song(fn)

player = ffmpeg.createPlayer()
player.queue = songs()
player.playing = True

import time
while True:
	time.sleep(1)
