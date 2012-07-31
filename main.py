#!/usr/bin/python

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

class Actions:
	def play(self, song):
		# via ffmpeg or so. load dynamically (ctypes)
		pass
		
		
	def pause(self): pass
	def next(self): pass
	def forward10s(self): pass

actions = Actions()

class initBy(property):
	def __init__(self, initFunc):
		property.__init__(self, fget = self.fget)
		self.initFunc = initFunc
	def fget(self, inst):
		if hasattr(self, "value"): return self.value
		self.value = self.initFunc()
		return self.value
	
class State:
	queue = initBy(loadQueue)
	recentlyPlayedList = initBy(loadRecentlyplayedList)
	
	playState = oneOf(
		"playing",
		"paused"
	)
	
state = State()

if __name__ == '__main__':
	startThread(tracker)
	main()
	