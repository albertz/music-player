from Song import Song

# http://code.google.com/p/leveldb/
# http://code.google.com/p/py-leveldb/
import leveldb

import appinfo
import utils


# see <https://github.com/albertz/binstruct/> for documentation
import binstruct
def dbRepr(o): return binstruct.varEncode(o).tostring()
def dbUnRepr(s): return binstruct.varDecode(s)


class DB:
	def __init__(self, dir):
		self.db = leveldb.LevelDB(appinfo.userdir + "/" + dir, max_open_files=200)

	def __getitem__(self, item):
		return dbUnRepr(self.db.Get(dbRepr(item)))

	def __setitem__(self, key, value):
		self.db.Put(dbRepr(key), dbRepr(value))

	def __delitem__(self, key):
		self.db.Delete(dbRepr(key))

	def setdefault(self, key, value):
		if key in self:
			return self[key]
		else:
			self[key] = value
			return self[key]

	def rangeIter(self, key_from = None, key_to = None, include_value = True):
		if include_value:
			mapFunc = lambda key,value: (dbUnRepr(key), dbUnRepr(value))
		else:
			mapFunc = dbUnRepr
		return map(mapFunc, self.db.RangeIter(key_from, key_to, include_value))
		
def init():
	global songDb
	songDb = DB("songs.db")
	global songHashDb
	songHashDb = DB("songHashs.db")

def normalizedFilename(fn):
	import os
	fn = os.path.normpath(fn)
	userDir = os.path.expanduser("~")
	if fn.startswith(userDir):
		fn = "~" + fn[len(userDir):]
	return fn

def hash(s):
	# I thought about using some more fast Hash like MurmurHash.
	# But this is just simpler now.
	# CRC32 is too less, to much collisions. We want something here
	# which does almost never collide. The whole code in here will
	# mostly ignore collisions (the whole DB is optional, so this
	# shouldn't be a problem in case anyone ever gets a collsion).
	import hashlib
	return hashlib.sha1(s).digest()

# These functions should either return some False value or some non-empty string.
SongHashSources = [
	("a", lambda song: getattr(song, "fingerprint_AcoustID", None)),
	("p", lambda song: normalizedFilename(song.url)),
]

def getSongHashSources(song):
	for key,func in SongHashSources:
		value = func(song)
		if value: yield key + value
	
def getSongId(song):
	for value in getSongHashSources(song):
		try: return songHashDb[normalizedFilename(song.url)]
		except KeyError: pass
	return None

def calcNewSongId(song):
	"Returns a new unique (in hopefully almost all cases) id for a song."
	"Different files with the same song might return the same id."
	# Originally, I planned to use the hash of the AcoustID fingerprint.
	# However, as this is expensive to calculate in case we have not yet,
	# allow some fallbacks.
	# Just use any available from SongHashSources.
	for value in getSongHashSources(song):
		return value
	assert False # should not happen. if there are such cases later, extend SongHashSources!

def get(songId, attrib, timeout, accuracy, callback):
	pass


