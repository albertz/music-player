# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.


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

bmpWidth = 500
bmpHeight = 151
bgColor = (50,50,50)
timelineColor = (100,100,100)
timelineInterval = 5 # every 5 sec

assert os.path.isfile(filename)
import ffmpeg
duration, bmp = ffmpeg.calcBitmapThumbnail(Song(filename), bmpWidth, bmpHeight, bgColor, timelineColor, timelineInterval)

def formatTime(t):
	if t is None: return "?"
	mins = long(t // 60)
	t -= mins * 60
	hours = mins // 60
	mins -= hours * 60
	if hours: return "%02i:%02i:%02.0f" % (hours,mins,t)
	return "%02i:%02.0f" % (mins,t)

print filename, formatTime(duration)

open("thumbnail.bmp", "w").write(bmp)

os.system("open thumbnail.bmp")
