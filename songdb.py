# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# What DB backend to use? Many different DBs have been in discussion.
# Basically we just need a key/value store which should scale well.
# I.e. an inmemory-only DB such as Redis is probably not good as it would
# not allow very huge DBs because of memory limitations. Even if we would
# never hit that limit, I want the memory footprint of MusicPlayer very low,
# so this is not a good solution.
# * sqlite was initially discarded because we don't wanted a table like DB,
#   mostly because I want to have it easily extensible, i.e. adding new
#   keys (columns in a table) and probably the layout would be like a sparse
#   table or just a wrapper around a key/value-like store. Also for searching,
#   we would like to implement our own index to have full control over it.
#   And for this purpose, sqlite does not perform that well.
# * KyotoCabinet has good performance reports but unfortunately it is GPL
#   (or commercial). I don't want the GPL dependency, so it's not an option.
# * LevelDB looked like a good fit and has been used for a while. But unfortunately
#   I had often got corrupt databases when the player quit unexpectedly and
#   this is not acceptable.

# So, right now, we are still using sqlite as a key/value store because of
# stability and dependency-simplicity (sqlite comes with CPython).

import sqlite3



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



from Song import Song
import appinfo
import utils
from utils import safe_property

# see <https://github.com/albertz/binstruct/> for documentation
import binstruct
def dbRepr(o): return binstruct.varEncode(o).tostring()
def dbUnRepr(s): return binstruct.varDecode(s)


class DB(object):
	def __init__(self, name, create_command = "create table %s(key blob primary key unique, value blob)"):
		import threading
		self.writelock = threading.Lock()
		self.name = name
		self.path = appinfo.userdir + "/" + name
		self.create_command = create_command
		try:
			self.test()
		except Exception as exc:
			# Maybe we had an old LevelDB or some other corruption.
			# Not much we can do for recovering...
			print "DB %s opening error %r, I will reset the DB, sorry..." % (self.name, exc)
			self.removeOldDb()
			self.initNew()

		# We need a workaround wrapper for SQLite connection objects
		# because Python might crash in their tp_dealloc.
		# See <http://bugs.python.org/issue17263> for details.
		class LocalConnection:
			refs = set()
			lock = threading.RLock()			
			def __init__(self, conn):
				from weakref import ref
				self.conn = conn
				with self.lock:
					self.refs.add(ref(self))
					assert ref(self) in self.refs
			def get(self):
				with self.lock:
					return self.conn
			def reset(self):
				from weakref import ref
				with self.lock:
					self.refs.discard(ref(self))
					self.conn = None
			def __del__(self): self.reset()
			@classmethod
			def Reset(clazz):
				from weakref import ref
				with clazz.lock:
					for l in list(clazz.refs):
						l = l()
						if not l: continue
						l.reset()
		self.LocalConnection = LocalConnection

	@property
	def _connection(self):
		if not getattr(self, "_threadLocal", None):
			import threading
			self._threadLocal = threading.local()
		conn = getattr(self._threadLocal, "connection", None)
		if conn: return conn.get()
		return None
	
	@_connection.setter
	def _connection(self, v):
		if not getattr(self, "_threadLocal", None):
			import threading
			self._threadLocal = threading.local()
		setattr(self._threadLocal, "connection", self.LocalConnection(v))

	def test(self):
		# Some of these may throw an OperationalError.
		conn = sqlite3.connect(self.path)
		tblinfo = conn.execute("select sql from sqlite_master where type='table' and tbl_name='data'").fetchall()
		assert tblinfo, "DB main table not initialized"
		assert len(tblinfo) == 1, "DB main table not unique"
		sqlcmd = tblinfo[0][0]
		supposedsqlcmd = self.create_command % "data"
		assert sqlcmd.lower() == supposedsqlcmd.lower(), "DB main table was created with a different command (%s != %s)" % (sqlcmd, supposedsqlcmd)
		conn.execute("select * from data limit 1")
		
	def removeOldDb(self):
		# Maybe we really should do some backuping...?
		self.disconnectAll()
		import shutil, os
		shutil.rmtree(self.path, ignore_errors=True)
		try: os.remove(self.path)
		except OSError: pass
	
	def initNew(self):
		self.disconnectAll()
		conn = sqlite3.connect(self.path)
		with conn:
			conn.execute(self.create_command % "data")
	
	def _getConnection(self):
		if self._connection: return self._connection
		conn = sqlite3.connect(self.path)
		self._connection = conn
		return conn
	
	def _selectCmd(self, cmd, args):
		conn = self._getConnection()
		cur = conn.execute(cmd, args)
		return cur
	
	def _actionCmd(self, cmd, args):
		conn = self._getConnection()
		with conn:
			conn.execute(cmd, args)

	def __getitem__(self, key):
		key = dbRepr(key)
		key = buffer(key)
		cur = self._selectCmd("select value from data where key=? limit 1", (key,))
		value = cur.fetchone()
		if value is None: raise KeyError
		value = value[0]
		value = str(value)
		value = dbUnRepr(value)
		return value
	
	def __setitem__(self, key, value):
		key = dbRepr(key)
		key = buffer(key)
		value = dbRepr(value)
		value = buffer(value)
		self._actionCmd("replace into data values (?,?)", (key, value))
		
	def setdefault(self, key, value):
		if key in self:
			return self[key]
		else:
			self[key] = value
			return self[key]
		
	def disconnectAll(self):
		self.LocalConnection.Reset()
		self._threadLocal = None
		
	def flush(self):
		# Not sure if needed, I guess the commit already is the flush.
		# Closing all connections should in any case force the flush.
		self.disconnectAll()

DBs = {
	"songDb": lambda: DB("songs.db"),
	"songHashDb": lambda: DB("songHashs.db"),
	}

def usedDbsInCode(f):
	iterFunc = lambda: utils.iterGlobalsUsedInFunc(f, loadsOnly=True)
	import types
	if isinstance(f, (types.ClassType, types.TypeType)):
		iterFunc = lambda: utils.iterGlobalsUsedInClass(f, module=__name__)

	dbs = set() # there might be duplicates
	for name in iterFunc():
		if name in DBs:
			dbs.add(name)
	return dbs

def init():
	import threading
	for db in DBs.keys():
		globals()["_%s_initlock" % db] = threading.Lock()
		globals()[db] = None
	import types
	c = 0
	for name in globals().keys():
		v = globals()[name]
		if getattr(v, "__module__", None) != __name__:
			continue
		if isinstance(v, (types.FunctionType, types.ClassType, types.TypeType)):
			dbs = usedDbsInCode(v)
			if not dbs: continue
			#print "used dbs in", name, ":", dbs
			globals()[name] = lazyInitDb(*dbs)(v)
			c += 1
	assert c > 0, "check if __module__ is correct..."
	
def initDb(db):
	with globals()["_%s_initlock" % db]:
		if not globals()[db]:
			globals()[db] = DBs[db]()

def lazyInitDb(*dbs):
	def decorator(f):
		def decorated(*args, **kwargs):
			for db in dbs:
				initDb(db)
			return f(*args, **kwargs)
		return decorated
	return decorator

def initAllDbs():
	for db in DBs.keys():
		initDb(db)

def flush():
	for db in DBs.keys():
		db = globals()[db]
		if db:
			db.flush()
	
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
		try: songId = songHashDb[value]
		except KeyError: continue
		maybeInitSongDbEntry(song, songId)
		return songId
	return None

def maybeInitSongDbEntry(song, songId):
	import fileid
	nativeFileId = fileid.getFileNativeId(song.url)
	
	with songDb.writelock:
		change = False
		try: d = songDb[songId]
		except KeyError: d = {}
		filesDict = d.setdefault("files", {})
		fn = normalizedFilename(song.url)
		if not fn in filesDict:
			# init empty file-dict
			filesDict[fn] = {}
			change = True
		
		if nativeFileId and nativeFileId != filesDict[fn].get("nativeFileId", None):
			filesDict[fn]["nativeFileId"] = nativeFileId
			change = True
			
		if change:
			# save
			songDb[songId] = d
		
def updateHashDb(song, songId):
	for value in getSongHashSources(song):
		songHashDb[value] = songId
	maybeInitSongDbEntry(song, songId)
	
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
		object.__setattr__(self, "normalizedUrl", normalizedFilename(url))
	
	@safe_property
	@property
	def _dbDict(self):
		# Note: If this raises an AttributeError for some reason,
		# you will get a *very* strange inf recursion loop in
		# getattr(self, "_dbDict").
		return self.songEntry.files.filesDict.get(self.normalizedUrl, {})

	def __getattr__(self, attr):
		try: return self._dbDict[attr]
		except KeyError: raise AttributeError, "no attrib " + attr
	
	def update(self, attr, updateFunc, default=None):
		global songDb
		with songDb.writelock:
			d = self.songEntry._dbDict			
			fileDict = d.setdefault("files",{}).setdefault(self.normalizedUrl,{})
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
		except KeyError: raise KeyError
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
	import fileid
	def remapFilename(fn):
		expanded = os.path.expanduser(fn)
		if os.path.exists(expanded): return expanded
		nativeFileId = filesDict[fn].get("nativeFileId", None)
		if nativeFileId:
			path = fileid.getPathByNativeId(nativeFileId)
			if path and os.path.exists(path): return path
		return None
	files = map(remapFilename, files)
	files = filter(None, files)
	if not files: return None
	# priority: flac, m4a, ogg
	fsByExt = dict([(os.path.splitext(f)[1].lower(), f) for f in files])
	f = None
	for ext in [".flac",".m4a",".ogg"]:
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
	# Note: this assumes that we never have changed the normalize-func
	fileEntry = dbEntry["files"].get(normalizedFilename(f), {})
	# for now, this is just enough for good results in Search.Search.Keys
	songDict = {
		"url": f,
		"id": songId,
		"artist": dbEntry.get("artist", ""),
		"title": dbEntry.get("title", ""),
		"rating": Song(url=f).rating,
		"duration": fileEntry.get("duration", -1),
	}
	return songDict

class Attrib:
	def __init__(self, fileSpecific=False, type=None):
		self.fileSpecific = fileSpecific
		self.type = type
	def getObject(self, song):
		if self.fileSpecific:
			return getSong(song).files.get(song.url)
		else:
			return getSong(song)

Attribs = {
	# no id here. it's only local
	"artist": Attrib(type=unicode),
	"title": Attrib(type=unicode),
	"album": Attrib(type=unicode),
	"tags": Attrib(),
	"rating": Attrib(),
	"skipCount": Attrib(),
	"completedCount": Attrib(),
	"lastPlayedDate": Attrib(),
	"sha1": Attrib(fileSpecific=True),
	"metadata": Attrib(fileSpecific=True),
	"fingerprint_AcoustId": Attrib(fileSpecific=True),
	"nativeFileId": Attrib(fileSpecific=True),
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
	# If we ever want to allow None-values, mark it that way in class Attrib.
	# getattr should normally have raised AttributeError otherwise.
	assert value is not None, "songdb %r attrib %r is None" % (song, attrib)
	return value

Search_ResultLimit = 500
Search_SubtokenLimit = 6
Search_PrefixPostfixStrAttrIndex = 1 # (prefix,postfix) pairs
Search_ExtendTokenAttrIndex = 2 # (index,token) pairs
Search_SongAttrIndex = 3 # songid

def insertSearchEntry_raw(songId, tokens):
	global songSearchIndexDb

	def makeHashable(data):
		if isinstance(data, list):
			return tuple(map(makeHashable, data))
		return data

	# all entries sets. an update merges the sets
	def update(key, updates):
		with songSearchIndexDb.writelock:
			try: old = songSearchIndexDb[key]
			except KeyError: old = ()
			new = set(map(makeHashable, old))
			new.update(updates)
			songSearchIndexDb[key] = list(new)
	
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
			l *= 2
	
	def iterSubtokenFullExtensions(subTokenIdxs, tokenCount):
		if not isinstance(subTokenIdxs, tuple): subTokenIdxs = tuple(subTokenIdxs)
		for idx in range(tokenCount):
			if idx in subTokenIdxs: continue
			# index variance is max 1
			if min([abs(idx - i) for i in subTokenIdxs]) > 1: continue
			
			extended = tuple(sorted(subTokenIdxs + (idx,)))
			yield extended
			
			# fill in set because we will get duplicates
			moreExtendedSet = set()
			for moreExtended in iterSubtokenFullExtensions(extended, tokenCount):
				moreExtendedSet.add(moreExtended)
				
			for moreExtended in moreExtendedSet:
				yield moreExtended
	
	# subsequences of len 1,2,..,SubtokenLimit and then the full extensions
	import itertools
	def iterSubtokens(tokenCount):
		for n in range(1,Search_SubtokenLimit+1):
			if n > len(tokens): break
			for cmb in itertools.combinations(range(tokenCount), n):
				yield cmb
				if n == Search_SubtokenLimit: # now iter all full extensions
					for ext in iterSubtokenFullExtensions(cmb, tokenCount):
						yield ext
		
	import collections
	localUpdates = collections.defaultdict(set)
	
	for token in tokens:
		for subWord, prefix, postfix in iterSubwords(token):
			localUpdates[(Search_PrefixPostfixStrAttrIndex, subWord)].add((prefix, postfix))

	tokenCount = len(tokens)
	for subTokenIdxs in iterSubtokens(tokenCount):
		subTokens = tuple(tokens[i] for i in subTokenIdxs)
		for idx in range(tokenCount):
			if idx in subTokenIdxs: continue
			if len(subTokenIdxs) >= Search_SubtokenLimit:
				# only direct extensions. i.e. index variance is max 1
				if min([abs(idx - i) for i in subTokenIdxs]) > 1: continue
			
			insertIndex = 0
			while insertIndex < len(subTokenIdxs) and subTokenIdxs[insertIndex] < idx:
				insertIndex += 1
			newToken = tokens[idx]
			localUpdates[(Search_ExtendTokenAttrIndex, subTokens)].add((insertIndex, newToken))

	localUpdates[(Search_SongAttrIndex, tuple(tokens))].add(songId)

	for key,value in localUpdates.items():
		update(key, value)

def insertSearchEntry(song):
	tokens = song.artist.lower().split() + song.title.lower().split()
	insertSearchEntry_raw(song.id, tokens)
	
def search(query, limitResults=Search_ResultLimit, queryTokenMinLen=2):
	tokens = query.lower().split()
	tokens = filter(lambda t: len(t) >= queryTokenMinLen, tokens)
	if not tokens: return []
	
	def get(key, default=[]):
		try: return songSearchIndexDb[key]
		except KeyError: return default
	
	import math	
	class Token:
		def __init__(self, s):
			self.origString = s
			self.strings = []
			l = len(s)
			l2 = 2 ** int(math.log(l,2))
			if l2 != l: # it's not base2, take substring
				self.strings += [s[:l2]]
				self.newIndex = 1
			else:
				self.newIndex = 0			
			self.initIndex = 1 if l2 < l else 0
			self.strings += [s]
			self.expandIndex = 0
		def expand(self):
			oldStringCount = len(self.strings)
			self.newIndex = self.expandIndex
			for i in range(self.expandIndex, oldStringCount):
				for prefix,postfix in get((Search_PrefixPostfixStrAttrIndex,self.strings[i])):
					s = self.strings[i]
					s = prefix + s + postfix
					if s == self.origString: continue
					if len(s) > len(self.origString):
						if not self.origString in s: continue
					else:
						if not s in self.origString: continue
					self.strings += [s]
			self.expandIndex = oldStringCount
		@property
		def expanded(self): return self.expandIndex >= len(self.strings)
		@property
		def newWords(self): return self.strings[self.newIndex:]
		@property
		def words(self): return self.strings[self.initIndex:]
		def __repr__(self): return "<Token %r>" % self.strings
	tokenWords = map(Token, tokens[0:Search_SubtokenLimit])
	
	tokenListSet = set() # to keep track and avoid duplicates
	tokenLists = []
	tokenListIndex = 0
	
	class TokenList:
		def __init__(self, tokenList):
			self.tokenList = tokenList
		@property
		def expansions(self):
			for index,token in get((Search_ExtendTokenAttrIndex, self.tokenList)):
				yield self.tokenList[:index] + (token,) + self.tokenList[index:]
		@property
		def songs(self):
			for songId in get((Search_SongAttrIndex, self.tokenList)):
				yield songId
		@property
		def matchesQuery(self):
			if len(tokens) <= Search_SubtokenLimit:
				return True
			if len(self.tokenList) < len(tokens):
				return False
			i = 0
			for token in tokens:
				while i < len(self.tokenList) and token not in self.tokenList[i]:
					i += 1
				if i >= len(self.tokenList):
					return False
				i += 1
			return True
		def __repr__(self): return "<TokenList %r>" % list(self.tokenList)
	
	def addTokenList(tokenList):
		if tokenList in tokenListSet: return
		tokenListSet.add(tokenList)
		tokenLists.append(TokenList(tokenList))
		
	from itertools import product
	for tokenList in product(*[token.words for token in tokenWords]):
		addTokenList(tuple(tokenList))
	
	songs = set()
	songDescList = [] # list to keep the same order

	while True:
		newTokenListIndex = len(tokenLists)
		for i in range(tokenListIndex, len(tokenLists)):
			tokenList = tokenLists[i]
			for expTokenList in tokenList.expansions:
				addTokenList(expTokenList)
			if tokenList.matchesQuery:
				for songId in tokenList.songs:
					if not songId in songs:
						songs.add(songId)
						songDesc = getSongSummaryDictById(songId)
						if songDesc:
							songDescList += [songDesc]
				if len(songs) >= limitResults:
					break
		tokenListIndex = newTokenListIndex
			
		if len(songs) >= limitResults:
			break

		for i, token in enumerate(tokenWords):
			if not token.expanded:
				token.expand()

				if token.newWords:
					for tokenList in product(*(
						[t.words for t in tokenWords[:i]] +
						[token.newWords] +
						[t.words for t in tokenWords[i+1:]])):
						tokenLists.append(TokenList(tokenList))
		
		if all([token.expanded for token in tokenWords]) and tokenListIndex >= len(tokenLists):
			# nothing new anymore to explore
			break

	return songDescList


# These are search fallbacks while our own index doesn't work good enough.
# They use the sqlite FTS4 index.

DBs["songSearchIndexDb"] = lambda: DB(
	"songSearchIndex.db",
	create_command="CREATE VIRTUAL TABLE %s USING fts4(content TEXT, tokenize=porter)")
DBs["songSearchIndexRefDb"] = lambda: DB(
	"songSearchIndexRef.db",
	create_command="CREATE TABLE %s(rowid INTEGER PRIMARY KEY, songid BLOB UNIQUE)")

def insertSearchEntry_raw(songId, tokens):
	songId = buffer(songId)
	with songSearchIndexRefDb.writelock:
		rowId = songSearchIndexRefDb._selectCmd("select rowid from data where songid=?", (songId,)).fetchone()
		if rowId is not None:
			rowId = rowId[0]
		else:
			# insert new
			songSearchIndexRefDb._actionCmd("insert into data(songid) values(?)", (songId,))
			rowId = songSearchIndexRefDb._selectCmd("select rowid from data where songid=?", (songId,)).fetchone()
			assert rowId is not None
			rowId = rowId[0]
	tokens = " ".join(tokens)
	tokens = utils.simplifyString(tokens)
	songSearchIndexDb._actionCmd("replace into data(docid, content) values (?,?)", (rowId, tokens))

def search(query, limitResults=Search_ResultLimit):
	query = utils.simplifyString(query)
	cur = songSearchIndexDb._selectCmd("select docid from data where data match ? limit %i" % limitResults, (query,))
	results = [r[0] for r in cur]
	def getSongIdByRowId(rowId):
		songId = songSearchIndexRefDb._selectCmd("select songid from data where rowid=?", (rowId,)).fetchone()
		if songId is not None:
			songId = songId[0]
			return str(songId)
		return None
	results = map(getSongIdByRowId, results)
	results = map(getSongSummaryDictById, results)
	results = filter(None, results)
	return results

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
				insertSearchEntry(song)
		elif os.path.isdir(fullfn):
			indexSearchDir(fullfn)
			
def songdbMain():
	# This is heavy, ugly, etc...
	# But it's simple nice hack for now to index everything.
	def indexAll():
		import appinfo
		for dir in appinfo.musicdirs:
			utils.asyncCall(lambda: indexSearchDir(dir), name="create search index", mustExec=True)
	utils.daemonThreadCall(indexAll, name="create search index")
	
	# Reindex played songs.
	from State import state
	from player import PlayerEventCallbacks
	for ev,args,kwargs in state.updates.read():
		try:
			if ev is PlayerEventCallbacks.onSongChange:
				newSong = kwargs["newSong"]
				insertSearchEntry(newSong)
		except Exception:
			import sys
			sys.excepthook(*sys.exc_info())
	flush()
	
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

# Note: This doesn't load the DBs as earlier. This just setups the lazy loaders. See source.
init()
