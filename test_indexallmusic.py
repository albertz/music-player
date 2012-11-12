from Song import Song
import songdb
from utils import *
import appinfo
import better_exchook
better_exchook.install()

songdb.initAllDbs()

def indexSearchDir(dir):
	import os
	for fn in os.listdir(dir):
		fullfn = dir + "/" + fn
		if os.path.isfile(fullfn):
			ext = os.path.splitext(fn)[1].lower()
			if ext[:1] == ".": ext = ext[1:]
			if ext in appinfo.formats:
				song = Song(url=fullfn)
				assert song
				assert song.id
				songdb.insertSearchEntry(song)
				print "added", fn
		elif os.path.isdir(fullfn):
			indexSearchDir(fullfn)

for d in appinfo.musicdirs:
	indexSearchDir(d)
