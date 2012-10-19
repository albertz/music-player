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
#	song dict can contains (specified in code by global Attribs dict later):
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
	
# Entries (hash-prefix, attrib, func).
# The function should either return some False value or some non-empty string.
# If an attrib is specified and no func, we just use getattr(song, attrib, None).
SongHashSources = [
	("a", "fingerprint_AcoustID", None),
	("h", "sha1", None),
	("p", None, lambda song: normalizedFilename(song.url)),
]

def getSongHashSources(song):
	for prefix,attrib,func in SongHashSources:
		if not func: func = lambda song: getattr(song, attrib, None)
		value = func(song)
		if value: yield prefix + value	
	
def maybeUpdateHashAfterAttribUpdate(song, attrib, value):
	for prefix,attr,func in SongHashSources:
		if attr == attrib:
			songHashDb[prefix + value] = song.id
			return

def getSongId(song):
	for value in getSongHashSources(song):
		try: return songHashDb[value]
		except KeyError: pass
	return None

def updateHashDb(song, songId):
	for value in getSongHashSources(song):
		songHashDb[value] = songId

def calcNewSongId(song):
	"Returns a new unique (in hopefully almost all cases) id for a song."
	"Different files with the same song might return the same id."
	# Originally, I planned to use the hash of the AcoustID fingerprint.
	# However, as this is expensive to calculate in case we have not yet,
	# allow some fallbacks.
	# Just use any available from SongHashSources.
	for value in getSongHashSources(song):
		if len(value) > 32: value = hash(value)
		updateHashDb(song, value)
		return value
	assert False # should not happen. if there are such cases later, extend SongHashSources!

class SongFileEntry(object):
	def __init__(self, songEntry, url):
		object.__setattr__(self, "songEntry", songEntry)
		object.__setattr__(self, "url", url)
		
	@property
	def _dbDict(self):
		# Note: If this raises an AttributeError for some reason,
		# you will get a *very* strange inf recursion loop in
		# getattr(self, "_dbDict").
		return self.songEntry.files.filesDict.get(self.url, {})

	def __getattr__(self, attr):
		try: return self._dbDict[attr]
		except KeyError: raise AttributeError, "no attrib " + attr
		
	def __setattr__(self, attr, value):
		global songDb
		with songDb.writelock:
			d = self.songEntry._dbDict
			d.setdefault("files",{}).setdefault(self.url,{})[attr] = value
			songDb[self.songEntry.id] = d

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
	
	def get(self, url):
		url = normalizedFilename(url)
		return SongFileEntry(self.songEntry, url)
	
class SongEntry(object):
	def __init__(self, song):
		object.__setattr__(self, "songObj", song)
	
	@property
	def id(self):
		return self.songObj.id

	@property
	def files(self):
		return SongFilesDict(self)

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
			songDb[self.id] = d
	
def getSong(song):
	return SongEntry(song)

class Attrib:
	def __init__(self, fileSpecific=False):
		self.fileSpecific = fileSpecific
	def getObject(self, song):
		if self.fileSpecific:
			return getSong(song).files.get(song.url)
		else:
			return getSong(song)

Attribs = {
	"id": Attrib(), # This is the SongId used here by the DB.
	"artist": Attrib(),
	"title": Attrib(),
	"album": Attrib(),
	"tags": Attrib(),
	"rating": Attrib(),
	"sha1": Attrib(fileSpecific=True),
	"metadata": Attrib(fileSpecific=True),
	"fingerprint_AcoustId": Attrib(fileSpecific=True),
	"gain": Attrib(fileSpecific=True),
# Note that bmpThumbnail is not here. I think it's to heavy
# to be stored for each song in the DB. Let's just calculate it
# on the fly when needed...
# The Song handling code should not assume that all attribs are
# defined here by the DB.
}


def updateSongAttribValue(song, attrib, value):
	setattr(Attribs[attrib].getObject(song), attrib, value)
	maybeUpdateHashAfterAttribUpdate(song, attrib, value)

def getSongAttrib(song, attrib):
	return getattr(Attribs[attrib].getObject(song), attrib)
	
# Do that right on first import so that all functions here work.
init()

def songdbMain():
	# Later, me might scan through the disc and fill the DB and do updates here.
	# Right now, we don't.
	pass

# For debugging
def dumpDatabases():
	global songDb, songHashDb
	from pprint import pprint
	print "Main DB:"
	for key,value in songDb.rangeIter():
		sys.stdout.write("%r: " % key)
		pprint(value)
	print "\nHashes:"
	for key,value in songHashDb.rangeIter():
		sys.stdout.write("%r: " % key)
		pprint(value)

