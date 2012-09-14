

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

import sys, os

if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
	filename = sys.argv[1]
else:
	files = [
		"/Users/az/Music/Classic/Glenn Gould Plays Bach/Two- & Three-Part Inventions - Gould/19 Bach - Invention 13 in a (BWV 784).mp3",
		"/Users/az/Music/Rock/Tool/Lateralus/09 Lateralus.flac",
		"/Users/az/Music/Cults - Cults 7/Cults - Cults 7- - 03 The Curse.flac",
		"/Users/az/Music/Special/zorba/(01) - Theme From Zorba The Greek.ogg",
		"/Users/az/Music/Classic/Glenn Gould Plays Bach/French Suites, BWV812-7 - Gould/Bach, French Suite 5 in G, BWV816 - 5 Bourree.mp3",
		"/Users/az/Music/Electronic/Von Paul Kalkbrenner - Aaron.mp3",
		"/Users/az/Music/Electronic/One Day_Reckoning Song (Wankelmut Remix) - Asaf Avidan & the Mojos.mp3",
	]
	i = 5
	if len(sys.argv) >= 2: i = int(sys.argv[1])
	filename = files[i]

assert os.path.isfile(filename)
import ffmpeg
duration, bmp = ffmpeg.calcBitmapThumbnail(Song(filename))

open("thumbnail.bmp", "w").write(bmp)

os.system("open thumbnail.bmp")
