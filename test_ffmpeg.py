# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.
import better_exchook
better_exchook.install()

import ffmpeg

# ffmpeg log levels: {0:panic, 8:fatal, 16:error, 24:warning, 32:info, 40:verbose}
ffmpeg.setFfmpegLogLevel(20)

try:
	import faulthandler
	faulthandler.enable(all_threads=True)
except ImportError:
	print "note: module faulthandler not available"
	
class Song:
	def __init__(self, fn):
		self.url = fn
		self.f = open(fn)
		
	def __eq__(self, other):
		return self.url == other.url
	
	def readPacket(self, bufSize):
		s = self.f.read(bufSize)
		#print "readPacket", self, bufSize, len(s)
		return s

	def seekRaw(self, offset, whence):
		r = self.f.seek(offset, whence)
		#print "seekRaw", self, offset, whence, r, self.f.tell()
		return self.f.tell()

files = [
	"~/Music/Classic/Glenn Gould Plays Bach/Two- & Three-Part Inventions - Gould/19 Bach - Invention 13 in a (BWV 784).mp3",
	"~/Music/Rock/Tool/Lateralus/09 Lateralus.flac",
	"~/Music/Special/zorba/(01) - Theme From Zorba The Greek.ogg",
	"~/Music/Classic/Glenn Gould Plays Bach/French Suites, BWV812-7 - Gould/Bach, French Suite 5 in G, BWV816 - 5 Bourree.mp3",
	"~/Music/Electronic/Von Paul Kalkbrenner - Aaron.mp3",
	"~/Music/Electronic/One Day_Reckoning Song (Wankelmut Remix) - Asaf Avidan & the Mojos.mp3",
]
import sys
files = sys.argv[1:] + files
import os
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

player = ffmpeg.createPlayer()
player.outSamplerate = 48000
player.queue = songs()
player.peekQueue = peekSongs
player.playing = True

def formatTime(t):
	if t is None: return "?"
	mins = long(t // 60)
	t -= mins * 60
	hours = mins // 60
	mins -= hours * 60
	if hours: return "%02i:%02i:%02.0f" % (hours,mins,t)
	return "%02i:%02.0f" % (mins,t)

import termios

def prepareStdin():
	fd = sys.stdin.fileno()
	
	if os.isatty(fd):		
		old = termios.tcgetattr(fd)
		new = termios.tcgetattr(fd)
		new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
		# http://www.unixguide.net/unix/programming/3.6.2.shtml
		#new[6] [termios.VMIN] = 1
		#new[6] [termios.VTIME] = 0
		new[6] [termios.VMIN] = 0
		#timeout *= 10 # 10ths of second
		#if timeout > 0 and timeout < 1: timeout = 1
		timeout = 1
		new[6] [termios.VTIME] = timeout
		
		termios.tcsetattr(fd, termios.TCSANOW, new)
		termios.tcsendbreak(fd,0)

		import atexit
		atexit.register(lambda: termios.tcsetattr(fd, termios.TCSANOW, old))	

def getchar(timeout = 0):
	fd = sys.stdin.fileno()
	ch = os.read(fd,7)
	return(ch)

prepareStdin()

import time
#sys.stdout.write("\n")
while True:
	sys.stdout.write("\r\033[K") # clear line
	if player.playing: sys.stdout.write("playing, ")
	else: sys.stdout.write("paused, ")
	curSong = player.curSong
	if curSong:
		sys.stdout.write(
			os.path.basename(curSong.url) + " : " +
			formatTime(player.curSongPos) + " / " +
			formatTime(player.curSongLen))
	else:
		sys.stdout.write("no song")
	
	# time.sleep(0.05)
	ch = getchar(0.1)
	#sys.stdout.write(" " + repr(ch))
	if ch == "\x1b[D": # left
		player.seekRel(-10)
	elif ch == "\x1b[C": #right
		player.seekRel(10)
	elif ch == "\x1b[A": #up
		pass
	elif ch == "\x1b[B": #down
		pass
	elif ch == "\n": # return
		player.nextSong()
	elif ch == " ":
		player.playing = not player.playing
	elif ch == "q":
		print
		sys.exit(0)
	sys.stdout.flush()
