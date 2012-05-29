#!/usr/bin/python

queue = loadQueue()
recentyplayedList = loadRecentlyplayedList()

def play(song):
	# via ffmpeg or so. load dynamically (ctypes)
	pass

def main():
	while True:
		play(head(queue))	
		fillQueue(queue)
	
def track(event):
	# Last.fm or so
	pass
	
def tracker():
	for ev in mainStateChanges():
		track(ev)
		
if __name__ == '__main__':
	startThread(tracker)
	main()
	