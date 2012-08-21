import ffmpeg

class Song:
	def __init__(self, fn):
		self.url = fn
		self.f = open(fn)
		
	def readPacket(self, bufSize):
		s = self.f.read(bufSize)
		#print "readPacket", self, bufSize, len(s)
		return s

	def seekRaw(self, offset, whence):
		r = self.f.seek(offset, whence)
		#print "seekRaw", self, offset, whence, r, self.f.tell()
		return self.f.tell()
		
def songs():
	files = [
		"/Users/az/Music/Classic/Glenn Gould Plays Bach/Two- & Three-Part Inventions - Gould/19 Bach - Invention 13 in a (BWV 784).mp3",
		"/Users/az/Music/Rock/Tool/Lateralus/09 Lateralus.flac",
		"/Users/az/Music/Cults - Cults 7/Cults - Cults 7- - 03 The Curse.flac",
		"/Users/az/Music/Special/zorba/(01) - Theme From Zorba The Greek.ogg",
		"/Users/az/Music/Classic/Glenn Gould Plays Bach/French Suites, BWV812-7 - Gould/Bach, French Suite 5 in G, BWV816 - 5 Bourree.mp3",
		"/Users/az/Music/Electronic/Von Paul Kalkbrenner - Aaron.mp3",
		"/Users/az/Music/Electronic/One Day_Reckoning Song (Wankelmut Remix) - Asaf Avidan & the Mojos.mp3",
	]
	i = 0
	while True:
		yield Song(files[i])
		i += 1
		if i >= len(files): i = 0

player = ffmpeg.createPlayer()
player.queue = songs()
player.playing = True

def formatTime(t):
	if t is None: return "?"
	mins = long(t // 60)
	t -= mins * 60
	hours = mins // 60
	mins -= hours * 60
	if hours: return "%02i:%02i:%02.0f" % (hours,mins,t)
	return "%02i:%02.0f" % (mins,t)

import os,sys,termios

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
	
def getchar(timeout = 0):
	fd = sys.stdin.fileno()
	ch = os.read(fd,7)
	return(ch)

prepareStdin()

import time
sys.stdout.write("\n")
while True:
	sys.stdout.write("\r\033[K") # clear line
	if player.playing: sys.stdout.write("playing, ")
	else: sys.stdout.write("not playing, ")
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
	sys.stdout.flush()
