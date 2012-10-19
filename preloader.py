

PreloadNextN = 5

import sys

Attribs = ["gain", "bmpThumbnail", "fingerprint_AcoustID", "sha1"]

def needUpdate(song):
	for attr in Attribs:		
		if getattr(song, attr, None) is None: return True
	return False

def update(song):
	import threading
	curThread = threading.currentThread()
	for attr in Attribs:		
		if curThread.cancel: return
		if getattr(song, attr, None) is None:
			song.calcAndSet(attr)

def checkUpdate():
	from queue import queue
	from State import state
	
	songs = [state.curSong]
	songs += queue.peekNextN(PreloadNextN)
	
	import threading
	curThread = threading.currentThread()
	
	for song in songs:
		if song is None: continue
		if curThread.cancel: return
		if needUpdate(song):
			update(song)
		
def preloaderMain():
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
	
