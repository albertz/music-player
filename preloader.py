

PreloadNextN = 5

import sys

def needUpdate(song):
	if getattr(song, "bmpThumbnail", None) is None: return True
	if getattr(song, "fingerprint_AcoustID", None) is None: return True
	if getattr(song, "gain", None) is None: return True
	return False

def update(song):
	def doCalc(queue):
		try:
			import ffmpeg

			if getattr(song, "gain", None) is None:
				song.close()
				song.openFile() # this is another process, so safe
				duration, gain = ffmpeg.calcReplayGain(song)
				queue.put(("duration", duration))
				queue.put(("gain", gain))
				song.gain = gain # useful for bmpThumbnail
				
			if getattr(song, "bmpThumbnail", None) is None:
				song.close()
				song.openFile() # this is another process, so safe
				# We have song.gain which mostly lowers the volume. So increase here for nicer display.
				duration, bmpData = ffmpeg.calcBitmapThumbnail(song, 600, 81, volume = 1.5)
				queue.put(("duration", duration))
				queue.put(("bmpThumbnail", bmpData))

			if getattr(song, "fingerprint_AcoustID", None) is None:
				song.close()
				song.openFile()
				song.gain = 0 # just use original
				duration, fingerprint = ffmpeg.calcAcoustIdFingerprint(song)
				queue.put(("duration", duration))
				queue.put(("fingerprint_AcoustID", fingerprint))

		except:
			sys.excepthook(*sys.exc_info())
			
		queue.put((None,None))

	from multiprocessing import Process, Queue
	queue = Queue()
	Process(target=doCalc, args=(queue,)).start()
	
	while True:
		attr, value = queue.get()
		if attr is None: break
		setattr(song, attr, value)

def checkUpdate():
	from queue import queue
	from State import state
	
	songs = [state.curSong]
	songs += queue.peekNextN(PreloadNextN)
	
	for song in songs:
		if song is None: continue
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
	

