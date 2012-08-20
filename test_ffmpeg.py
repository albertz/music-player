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
		"/Users/az/Music/Cults - Cults 7/Cults - Cults 7- - 03 The Curse.flac",
		"/Users/az/Music/Rock/Tool/Lateralus/09 Lateralus.flac",
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
	if hours: return "%02i:%02i:%05.2f" % (hours,mins,t)
	return "%02i:%05.2f" % (mins,t)
	
import time, os, sys
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
	sys.stdout.flush()
	time.sleep(0.05)
