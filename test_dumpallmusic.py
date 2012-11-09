from Song import Song
import songdb
from utils import *
import appinfo
import better_exchook
better_exchook.install()

try:
	songdb.initAllDbs()
	useDb = True
except Exception:
	# this might fail for various reasons. e.g. the DB might be locked by the player.
	# ignore then
	useDb = False

def doDir(dir):
	import os
	for fn in os.listdir(dir):
		fullfn = dir + "/" + fn
		if os.path.isfile(fullfn):
			ext = os.path.splitext(fn)[1].lower()
			if ext[:1] == ".": ext = ext[1:]
			if ext in appinfo.formats:
				song = Song(url=fullfn, _useDb=useDb)
				assert song
				songDict = {
					"url": fullfn,
					"artist": song.artist,
					"title": song.title,
				}
				if useDb:
					assert song.id
					songDict["id"] = song.id
				print betterRepr(songDict), ","
		elif os.path.isdir(fullfn):
			 doDir(fullfn)

print "["
for d in appinfo.musicdirs:
	doDir(d)
print "]"
