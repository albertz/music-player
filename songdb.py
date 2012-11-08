from Song import Song

# http://code.google.com/p/leveldb/
# http://code.google.com/p/py-leveldb/
import leveldb

import appinfo
import utils
from utils import safe_property


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
		self.db.Delete(dbRepr(key))

	def setdefault(self, key, value):
		if key in self:
			return self[key]
		else:
			self[key] = value
			return self[key]
		
	def rangeIter(self, key_from = None, key_to = None, include_value = True):
		def saveDbUnRepr(v):
			try: return dbUnRepr(v)
			except: return None # not/broken binstruct data			
		if include_value:
			mapFunc = lambda value: (saveDbUnRepr(value[0]), saveDbUnRepr(value[1]))
		else:
			mapFunc = saveDbUnRepr
		return map(mapFunc, self.db.RangeIter(key_from, key_to, include_value))
		
def init():
	global songDb
	songDb = DB("songs.db")
	global songHashDb
	songHashDb = DB("songHashs.db")
	global songSearchIndexDb
	songSearchIndexDb = DB("songSearchIndex.db")

def normalizedFilename(fn):
	import os
	fn = os.path.normpath(fn)
	userDir = os.path.expanduser("~")
	if fn.startswith(userDir):
		fn = "~" + fn[len(userDir):]
	if isinstance(fn, unicode): fn = fn.encode("utf-8")
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
	("a", "fingerprint_AcoustId", None),
	("h", "sha1", None),
	("p", None, lambda song: normalizedFilename(song.url)),
]

def mapHash(value):
	if isinstance(value, unicode): value = value.encode("utf-8")
	if len(value) > 32: value = hash(value)
	return value

def getSongHashSources(song):
	for prefix,attrib,func in SongHashSources:
		if not func: func = lambda song: getattr(song, attrib, None)
		value = func(song)
		if value: yield prefix + mapHash(value)
	
def maybeUpdateHashAfterAttribUpdate(song, attrib, value):
	for prefix,attr,func in SongHashSources:
		if attr == attrib:
			hashDbKey = prefix + mapHash(value)
			try:
				oldId = songHashDb[hashDbKey]
				if oldId != song.id:
					# whoops, we had a wrong song.id before...
					# update it.
					# we might loose some data which was set in the meantime,
					# but i don't really know a good way to solve this...
					song.id = oldId
					updateHashDb(song, song.id)
			except KeyError:
				songHashDb[hashDbKey] = song.id
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
		value = mapHash(value)
		updateHashDb(song, value)
		return value
	assert False # should not happen. if there are such cases later, extend SongHashSources!

class SongFileEntry(object):
	def __init__(self, songEntry, url):
		object.__setattr__(self, "songEntry", songEntry)
		object.__setattr__(self, "url", url)
	
	@safe_property
	@property
	def _dbDict(self):
		# Note: If this raises an AttributeError for some reason,
		# you will get a *very* strange inf recursion loop in
		# getattr(self, "_dbDict").
		return self.songEntry.files.filesDict.get(self.url, {})

	def __getattr__(self, attr):
		try: return self._dbDict[attr]
		except KeyError: raise AttributeError, "no attrib " + attr
	
	def update(self, attr, updateFunc, default=None):
		global songDb
		with songDb.writelock:
			d = self.songEntry._dbDict
			fileDict = d.setdefault("files",{}).setdefault(self.url,{})
			value = updateFunc(fileDict.get(attr, default))
			fileDict[attr] = value
			songDb[self.songEntry.id] = d
		return value
	
	def __setattr__(self, attr, value):
		self.update(attr, lambda _: value)
			
class SongFilesDict:
	def __init__(self, songEntry):
		self.songEntry = songEntry
		
	@safe_property
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
	
	@safe_property
	@property
	def id(self):
		return self.songObj.id

	@safe_property
	@property
	def files(self):
		return SongFilesDict(self)

	@safe_property
	@property
	def _dbDict(self):
		global songDb
		try: return songDb[self.id]
		except KeyError: return {}
		
	def __getattr__(self, attr):
		try: return self._dbDict[attr]
		except KeyError: raise AttributeError, "no attrib " + attr

	def update(self, attr, updateFunc, default=None):
		global songDb
		with songDb.writelock:
			d = self._dbDict
			value = updateFunc(d.get(attr, default))
			d[attr] = value
			songDb[self.id] = d		
		return value
	
	def __setattr__(self, attr, value):
		self.update(attr, lambda _: value)
	
def getSong(song):
	return SongEntry(song)

def getBestSongFileFromDict(filesDict):
	files = filesDict.keys()
	import os
	files = map(os.path.expanduser, files)
	files = filter(os.path.exists, files)
	if not files: return None
	# priority: flac, m4a, ogg
	fsByExt = dict([(os.path.splitext(f)[1].lower(), f) for f in files])
	f = None
	for ext in ["flac","m4a","ogg"]:
		f = fsByExt.get(ext, None)
		if f: break
	if not f: f = files[0] # just take first, whatever that is
	assert f
	return f
	
def getSongFilenameById(songId):
	global songDb
	try: dbEntry = songDb[songId]
	except KeyError: return None
	filesDict = dbEntry.get("files",{})
	return getBestSongFileFromList(filesDict)

def getSongById(songId):
	f = getSongFilenameById(songId)
	if not f: return None
	song = Song(url=f)
	song.id = songId
	assert song
	return song

def getSongSummaryDictById(songId):
	global songDb
	try: dbEntry = songDb[songId]
	except KeyError: return None
	f = getBestSongFileFromDict(dbEntry.get("files",{}))
	if not f: return None
	fileEntry = dbEntry["files"][normalizedFilename(f)] # Note: this assumes that we never have changed the normalize-func
	# for now, this is just enough for good results in Search.Search.Keys
	return {
		"url": f,
		"id": songId,
		"artist": dbEntry.get("artist", ""),
		"title": dbEntry.get("title", ""),
		"rating": dbEntry.get("rating", 0),
		"duration": fileEntry.get("duration", -1),
	}

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
	"skipCount": Attrib(),
	"completedCount": Attrib(),
	"lastPlayedDate": Attrib(),
	"sha1": Attrib(fileSpecific=True),
	"metadata": Attrib(fileSpecific=True),
	"fingerprint_AcoustId": Attrib(fileSpecific=True),
	"gain": Attrib(fileSpecific=True),
	"duration": Attrib(fileSpecific=True),
# Note that bmpThumbnail is not here. I think it's to heavy
# to be stored for each song in the DB. Let's just calculate it
# on the fly when needed...
# The Song handling code should not assume that all attribs are
# defined here by the DB.
}


def updateSongAttribValue(song, attrib, updateFunc, default=None):
	value = Attribs[attrib].getObject(song).update(attrib, updateFunc, default=default)
	maybeUpdateHashAfterAttribUpdate(song, attrib, value)
	return value

def getSongAttrib(song, attrib):
	value = getattr(Attribs[attrib].getObject(song), attrib)
	assert value is not None, "songdb %r attrib %r is None" % (song, attrib) # if we ever want to allow that, mark it that way in class Attrib
	return value

Search_SubtokenLimit = 6
Search_PrefixPostfixStrAttrIndex = 1
Search_PrefixTokenAttrIndex = 2
Search_PostfixTokenAttrIndex = 3
Search_SongAttrIndex = 4

def insertSearchEntry(song):
	global songSearchIndexDb

	# all entries sets. an update merges the sets
	def update(key, updates):
		with songSearchIndexDb.writelock:
			old = songSearchIndexDb[key]
			old = set(old)
			old.update(updates)
			songSearchIndexDb[key] = old
	
	# subwords of len 1,2,4,8,16,... so we need O(n * log n) subwords for n=wordLen
	def iterSubwords(word):
		wordLen = len(word)
		l = 1
		while l < wordLen:
			for i in range(wordLen - l + 1):
				subWord = word[i:i+l]
				j = max(0, i - l)
				prefix = word[j:i]
				j = min(wordLen, i + 2*l - len(prefix))
				postfix = word[i+l:j]
				yield (subWord, prefix, postfix)
			l **= 2
	
	# subsequences of len 1,2,..,SubtokenLimit
	import itertools
	def iterSubtokens(tokens):
		for i in range(Search_SubtokenLimit):
			if i > len(tokens): break
			for cmb in itertools.combinations(tokens, i):
				yield cmb
	
	tokens = song.artist.lower().split() + song.title.lower().split()
	
	import collections
	localUpdates = collections.defaultdict(set)
	
	for token in tokens:
		for subWord, prefix, postfix in iterSubwords(token):
			localUpdates[(Search_PrefixPostfixStrAttrIndex, subWord)].add((prefix, postfix),)

	for subTokens in iterSubtokens(tokens):
		localUpdates[(Search_PrefixTokenAttrIndex, subWord)].add((prefix, postfix),)

	for key,value in localUpdates.items():
		update(key, value)
	
def search(query):
	return [{"title": "hey", "artist": query, "url": "/Users/az/README.md"}, {"title": "foo"}]
	
# Do that right on first import so that all functions here work.
init()

def songdbMain():
	# Later, me might scan through the disc and fill the DB and do updates here.
	# Right now, we don't.
	pass

# For debugging
def dumpDatabases():
	global songDb, songHashDb
	import sys
	from pprint import pprint
	print "Main DB:"
	for key,value in songDb.rangeIter():
		sys.stdout.write("%r: \n" % key)
		pprint(value, indent=2)
	print "\nHashes:"
	for key,value in songHashDb.rangeIter():
		sys.stdout.write("%r: " % key)
		pprint(value, indent=2)

