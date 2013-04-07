# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.
import better_exchook
better_exchook.install()

import sys, os, time
import ffmpeg
player = ffmpeg.createPlayer()

# Check if ffmpeg player is supported, i.e. version recent enough.
assert hasattr(player, "soundcardOutputEnabled")
assert hasattr(player, "nextSongOnEof")
assert hasattr(player, "readOutStream")


finished = False

def onSongChange(*args, **kwargs):
	# Don't load next song once the first one finished.
	player.nextSongOnEof = False
	
def onSongFinished(*args, **kwargs):
	global finished
	finished = True
	
player.onSongChange = onSongChange
player.onSongFinished = onSongFinished

class Song:
	def __init__(self, fn):
		self.url = fn
		self.f = open(fn)
	def __repr__(self):
		return "<Song %s>" % os.path.basename(self.url)
	def __eq__(self, other):
		return self.url == other.url
	def readPacket(self, bufSize):
		return self.f.read(bufSize)
	def seekRaw(self, offset, whence):
		self.f.seek(offset, whence)
		return self.f.tell()

files = [
	"~/Music/Electronic/28C3/[MA054] Dirk GlÅcksberg - Planet Red/03 Dirk GlÅcksberg - Found And Lost.mp3",
	"~/Music/Rock/Nine Inch Nails/The Fragile (Left)/Nine Inch Nails - The Fragile (Left) - 11 - La Mer.mp3",
	"~/Music/Classic/Glenn Gould Plays Bach/Two- & Three-Part Inventions - Gould/19 Bach - Invention 13 in a (BWV 784).mp3",
	"~/Music/Rock/Tool/Lateralus/09 Lateralus.flac",
	"~/Music/Cults - Cults 7/Cults - Cults 7- - 03 The Curse.flac",
	"~/Music/Electronic/Von Paul Kalkbrenner - Aaron.mp3",
	"~/Music/Electronic/One Day_Reckoning Song (Wankelmut Remix) - Asaf Avidan & the Mojos.mp3",
]
files = sys.argv[1:] + files
files = map(os.path.expanduser, files)
i = 0

def songs():
	global i, files
	while True:
		yield Song(files[i])
		i += 1
		if i >= len(files): i = 0

def peekSongs(n):
	nexti = i + 1
	if nexti >= len(files): nexti = 0
	return map(Song, files[nexti:] + files[:nexti])

player.outSamplerate = 48000
player.queue = songs()
#player.peekQueue = peekSongs


# Don't stream the data to the sound card.
# This enables us to use use readOutStream.
player.soundcardOutputEnabled = False



def formatTime(t):
	if t is None: return "?"
	mins = long(t // 60)
	t -= mins * 60
	hours = mins // 60
	mins -= hours * 60
	if hours: return "%02i:%02i:%02.0f" % (hours,mins,t)
	return "%02i:%02.0f" % (mins,t)

def printPos():
	try:
		proc = 100.0 * player.curSongPos / player.curSongLen
	except TypeError:
		proc = 0
	sys.stdout.write("%r: %i%%, %s / %s" % ( 
		player.curSong,
		proc,
		formatTime(player.curSongPos),
		formatTime(player.curSongLen)
	))
	sys.stdout.flush()

# Start the encoder thread.
player.playing = True

printPos()
while not finished:
	buf = player.readOutStream()
	if len(buf) == 0:
		# Let's wait a bit to fill the stream.
		time.sleep(0.1)
		continue
	#print len(buf), repr(buf[0:20])

	sys.stdout.write("\r\033[K") # clear line
	printPos()
print
print "song finished"
