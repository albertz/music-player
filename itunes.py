
# https://github.com/albertz/itunes-scripts
# by Albert Zeyer, www.az2000.de
# code under GPLv3+

import sys
import codecs # utf8
import os

try:
	libraryXmlFile = codecs.open(os.path.expanduser("~/Music/iTunes/iTunes Music Library.xml"), "r", "utf-8")
except:
	sys.excepthook(*sys.exc_info())
	libraryXmlFile = None

def parse_xml(stream):
	state = 0
	spaces = " \t\n"
	data = ""
	node = ""
	nodeprefix = ""
	nodepostfix = ""
	nodeargs = []
	while True:
		c = stream.read(1)
		if c == "": break

		oldstate = state
		if state == 0:
			if c == "<": state = 1
			else: data += c
		elif state == 1: # in node
			if c in spaces:
				if node == "": pass
				else: state = 2
			elif c in "!/?":
				if node == "": nodeprefix += c
				else: nodepostfix += c
			elif c == ">": state = 0
			elif c == "\"": state = 3
			else: node += c
		elif state == 2: # in nodeargs
			if c in spaces: pass
			elif c == ">": state = 0
			elif c == "\"": state = 3
			elif c == "/": nodepostfix += c
			else:
				nodeargs.append(c)
				state = 4
		elif state == 3: # in nodearg str
			if c == "\\": state = 5
			elif c == "\"": state = 2
			else: pass # we dont store it right now
		elif state == 4: # in nodearg
			if c in spaces: state = 2
			elif c == ">": state = 0
			elif c == "\"": state = 3
			elif c == "/": nodepostfix += c
			else: nodeargs[-1] += c
		elif state == 5: # in escaped nodearg str
			# we dont store it right now
			state = 3

		if oldstate > 0 and state == 0:
			yield nodeprefix + node + nodepostfix, nodeargs, data
			nodeprefix, node, nodepostfix = "", "", ""
			nodeargs = []
			data = ""

import base64
def _plistDataConv(data):
	data = data.replace(" ", "")
	data = data.replace("\t", "")
	data = data.replace("\n", "")
	return base64.b64decode(data)

# code from here: http://wiki.python.org/moin/EscapingXml
import xml.parsers.expat
def xmlUnescape(s):
	want_unicode = False
	if isinstance(s, unicode):
		s = s.encode("utf-8")
		want_unicode = True

	# the rest of this assumes that `s` is UTF-8
	list = []

	# create and initialize a parser object
	p = xml.parsers.expat.ParserCreate("utf-8")
	p.buffer_text = True
	p.returns_unicode = want_unicode
	p.CharacterDataHandler = list.append

	# parse the data wrapped in a dummy element
	# (needed so the "document" is well-formed)
	p.Parse("<e>", 0)
	p.Parse(s, 0)
	p.Parse("</e>", 1)

	# join the extracted strings and return
	es = ""
	if want_unicode:
		es = u""
	return es.join(list)

plistPrimitiveTypes = {"integer": int, "real": float, "string": xmlUnescape, "date": str, "data": _plistDataConv}

def parse_plist_content(xmlIter, prefix, nodeExceptions = {}):
	for node, nodeargs, data in xmlIter:
		if node in nodeExceptions:
			raise nodeExceptions[node]
		elif node == "array":
			for entry in parse_plist_arrayContent(xmlIter, prefix): yield entry
		elif node == "dict":
			for entry in parse_plist_dictContent(xmlIter, prefix): yield entry
		elif node in plistPrimitiveTypes:
			for entry in parse_plist_primitiveContent(xmlIter, prefix, node): yield entry
		elif node == "true/":
			yield prefix, True
		elif node == "false/":
			yield prefix, False
		else:
			print >>sys.stderr, "didnt expected node", repr(node), "in content in prefix", repr(prefix)
		break
		
def parse_plist_primitiveContent(xmlIter, prefix, contentType):
	for node, nodeargs, data in xmlIter:
		if node == "/" + contentType:
			yield prefix, plistPrimitiveTypes[contentType](data)
		else:
			print >>sys.stderr, "didnt expected node", repr(node), "in primitive content", repr(contentType), "in prefix", repr(prefix)
		break

class PlistMarkerArrayBegin: pass
class PlistMarkerArrayEnd: pass

def parse_plist_arrayContent(xmlIter, prefix):
	yield prefix, PlistMarkerArrayBegin
	index = 0
	while True:
		try:
			for entry in parse_plist_content(xmlIter, prefix + [index], {"/array": PlistMarkerArrayEnd()}):
				yield entry
		except PlistMarkerArrayEnd:
			break
		index += 1
	yield prefix, PlistMarkerArrayEnd

class PlistMarkerDictBegin: pass
class PlistMarkerDictEnd: pass

# dict in plist is a list of key/value pairs
def parse_plist_dictContent(xmlIter, prefix):
	lastkey = None
	yield prefix, PlistMarkerDictBegin
	for node, nodeargs, data in xmlIter:
		if node == "key": pass
		elif node == "/key":
			if lastkey is not None: print >>sys.stderr, "expected value after key in dict content in prefix", repr(prefix)
			lastkey = data
			for entry in parse_plist_content(xmlIter, prefix + [lastkey]):
				yield entry
			lastkey = None
		elif node == "/dict": break
		else:
			print >>sys.stderr, "didn't expected node", repr(node), "in dict content in prefix", repr(prefix)
	yield prefix, PlistMarkerDictEnd

def parse_plist(xmlIter):
	for node, nodeargs, data in xmlIter:
		if node == "plist":
			for entry in parse_plist_content(xmlIter, []): yield entry

if libraryXmlFile:
	libraryPlistIter = parse_plist(parse_xml(libraryXmlFile))
else:
	libraryPlistIter = []

def songsIter(plistIter):
	for prefix, value in plistIter:
		if len(prefix) == 2 and prefix[0] == "Tracks" and value is PlistMarkerDictBegin:
			song = {}
			for prefix2, value2 in plistIter:
				if prefix2 == prefix and value2 is PlistMarkerDictEnd: break
				song[prefix2[2]] = value2
			if "Rating" not in song: song["Rating"] = None
			yield song

librarySongsIter = songsIter(libraryPlistIter)

def ratingsIter():
	import urllib
	import re
	for song in librarySongsIter:
		rating = song["Rating"]
		if rating is None: continue # print only songs with any rating set
		rating /= 100.0 # the maximum is 100
		fn = song["Location"]
		fn = urllib.unquote(fn)
		fn = re.sub("^file://(localhost)?", "", fn)
		yield (fn, rating)


if __name__ == "__main__":
	for fn, rating in ratingsIter():
		print rating, repr(fn)
	sys.exit()

def loadRatings():
	def doCalc(queue):
		for fn, rating in ratingsIter():
			queue.put((fn,rating))
		queue.put((None,None))
		
	from utils import AsyncTask
	queue = AsyncTask(func=doCalc, name="iTunes load ratings")
	
	while True:
		fn, rating = queue.get()
		if fn is None: return
		ratings[fn] = rating

# do some extra check in case we are reloading this module. don't reload the ratings. takes too long
try:
	loadRatingsThread
except NameError:
	ratings = {}
	from threading import Thread
	loadRatingsThread = Thread(target = loadRatings, name = "iTunes ratings loader")
	loadRatingsThread.daemon = True
	loadRatingsThread.start()
