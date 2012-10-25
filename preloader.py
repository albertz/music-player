

PreloadNextN = 10

import sys

Attribs = ["sha1", "gain", "fingerprint_AcoustId", "bmpThumbnail"]

def needUpdate(song):
	for attr in Attribs:		
		if getattr(song, attr, None) is None: return True
	return False

def update(song):
	import threading
	curThread = threading.currentThread()
	for attr in Attribs:		
		if curThread.cancel: return
		# This will calculate it and save it.
		song.get(
			attr,
			timeout=None, # wait for it. dont spawn too much tasks async
			)

def checkUpdate():
	from queue import queue
	from State import state
	
	import threading
	curThread = threading.currentThread()
	
	checkAgain = True
	while checkAgain:
		checkAgain = False
		songs = []
		if state.curSong:
			songs += [state.curSong]
		songs += queue.peekNextN(PreloadNextN)
				
		for song in songs:
			if song is None: continue
			if curThread.cancel: return
			if needUpdate(song):
				update(song)
				checkAgain = True
				break
		
def preloaderMain():
	try:
		# Import itunes module. This might start some background processes
		# which load the iTunes DB, etc.
		import itunes
	except:
		sys.excepthook(*sys.exc_info())
	
	try:
		checkUpdate()
	except:
		sys.excepthook(*sys.exc_info())
	
	from State import state
	for ev,args,kwargs in state.updates.read():
		try:
			# actually, the queue thread might not have added songs yet.
			# it might make more sense to yield queue updates here.
			# not possible atm, though. and this still works good enough.
			checkUpdate()
		except:
			sys.excepthook(*sys.exc_info())
	
