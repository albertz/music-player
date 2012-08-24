from utils import *
from Song import Song

player = None

def loadQueue(state):
	print "load queue"

	# dummy example from test_ffmpeg
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
			yield Song(files[i], state._main["player"])
			i += 1
			if i >= len(files): i = 0
	return songs()
	
def loadRecentlyplayedList(state):
	pass

class State:
	queue = initBy(loadQueue)
	recentlyPlayedList = initBy(loadRecentlyplayedList)
	
	playState = oneOf(
		"playing",
		"paused"
	)

	def __init__(self, main):
		self._main = main
		