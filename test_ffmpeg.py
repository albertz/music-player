import ffmpeg

class Song:
	pass

def songs():
	while True:
		yield Song()

player = ffmpeg.createPlayer()
player.queue = songs()
player.playing = True

import time
while True:
	time.sleep(1)
