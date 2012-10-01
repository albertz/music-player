import better_exchook
better_exchook.install()

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

if len(sys.argv) == 2:
	filename = sys.argv[1]
else:
	files = [
		"~/Music/Classic/Glenn Gould Plays Bach/Two- & Three-Part Inventions - Gould/19 Bach - Invention 13 in a (BWV 784).mp3",
		"~/Music/Rock/Tool/Lateralus/09 Lateralus.flac",
		"~/Music/Cults - Cults 7/Cults - Cults 7- - 03 The Curse.flac",
		"~/Music/Special/zorba/(01) - Theme From Zorba The Greek.ogg",
		"~/Music/Classic/Glenn Gould Plays Bach/French Suites, BWV812-7 - Gould/Bach, French Suite 5 in G, BWV816 - 5 Bourree.mp3",
		"~/Music/Electronic/Von Paul Kalkbrenner - Aaron.mp3",
		"~/Music/Electronic/One Day_Reckoning Song (Wankelmut Remix) - Asaf Avidan & the Mojos.mp3",
		"~/Music/Electronic/Swing & Electro Swing/Parov Stelar/2008 - Daylight (Japan Only)/03 - Charlestone Butterfly.flac", # this one has replaygain metadata
	]
	files = map(os.path.expanduser, files)
	filename = files[7]

print(os.path.basename(filename))
assert os.path.isfile(filename)

import ffmpeg
metadata = ffmpeg.getMetadata(Song(filename))
from pprint import pprint
pprint(metadata)

duration, replaygain = ffmpeg.calcReplayGain(Song(filename))
print("duration: %f" % duration)
print("replaygain: %f" % replaygain)

import math
x = replaygain
print x
x = 64.82 - x
print x
x = math.pow(10, x / 20)
print x
