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


# Structure of the database:
#	There is the main song db songs.db:
#		songId -> song dict
#	songId is any random string, not too long but long enough to avoid >99.999% collisions.
#	song dict can contains:
#		artist: str
#		title: str
#		album: str
#		tags: weighted tagmap, dict tag->[0,1]
#		rating: float in [0,1]
#		files: dict filename -> dict with entries:
#			sha1: str
#			metadata: dict
#			fingerprint_AcoustId: str
#			gain: float
#   values should only be stored if they are certain with best accurary

class DB:
	def __init__(self, dir):
		import threading
		self.writelock = threading.Lock()
		self.db = leveldb.LevelDB(appinfo.userdir + "/" + dir, max_open_files=200)

	def __getitem__(self, item):
		return dbUnRepr(self.db.Get(dbRepr(item)))

	def __setitem__(self, key, value):
		self.db.Put(dbRepr(key), dbRepr(value))

	def __delitem__(self, key):
		with self.lock:
			self.db.Delete(dbRepr(key))

	def setdefault(self, key, value):
		if key in self:
			return self[key]
		else:
			self[key] = value
			return self[key]

	def write(self, key, modifyFunc):
		with self.writelock:
			pass
		
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

HashFileBufferSize = 1024 * 10

def hashFile(f):
	if isinstance(f, (str,unicode)): f = open(f)
	import hashlib
	h = hashlib.sha1()
	while True:
		s = f.read(HashFileBufferSize)
		if not s: break
		h.update(s)
	return h.digest()
	
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
		if len(value) <= 32: return value
		return hash(value)
	assert False # should not happen. if there are such cases later, extend SongHashSources!

class SongFileEntry:
	def __init__(self, songEntry, url):
		self.songEntry = songEntry
		self.url = url
		
	@property
	def _dbDict(self):
		return self.songEntry.files[self.url].filesDict

	def __getattr__(self, attr):
		try: return self._dbDict[attr]
		except KeyError: raise AttributeError, "no attrib " + attr
	
	def __setattr__(self, attr, value):
		global songDb
		with songDb.writelock:
			d = self._dbDict
			d["files"][self.url][attr] = value
			songDb[attr] = d

class SongFilesDict:
	def __init__(self, songEntry):
		self.songEntry = songEntry
		
	@property
	def filesDict(self):
		return self.songEntry._dbDict.get("files", {})

	def __getitem__(self, url):
		url = normalizedFilename(url)
		try: self.filesDict[url]
		except: raise
		else: return SongFileEntry(self.songEntry, url)
	
class SongEntry:
	def __init__(self, song):
		self.songObj = song
		self._id = getSongId(song)
	
	@property
	def id(self):
		if not self._id:
			self._id = calcNewSongId(self.songObj)
		return self._id

	@property
	def files(self):
		return SongFileDict(self)

	@property
	def _dbDict(self):
		global songDb
		try: return songDb[self.id]
		except KeyError: return {}
		
	def __getattr__(self, attr):
		try: return self._dbDict[attr]
		except KeyError: raise AttributeError, "no attrib " + attr

	def __setattr__(self, attr, value):
		global songDb
		with songDb.writelock:
			d = self._dbDict
			d[attr] = value
			songDb[attr] = d
	
def getSong(song):
	return SongEntry(song)

def updateSongFileAttribValue(song, attrib, value):
	setattr(getSong(song).files[song.url], attrib, value)	

def getSongFileAttrib(song, attrib):
	return getattr(getSong(song).files[song.url], attrib)
	

# Do that right on first import so that all functions here work.
init()

def songdbMain():
	# Later, me might scan through the disc and fill the DB and do updates here.
	# Right now, we don't.
	pass
