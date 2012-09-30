import better_exchook
better_exchook.install()

class Song:
	def __init__(self, fn):
		self.url = fn
		self.f = open(fn)
	def readPacket(self, bufSize):
		s = self.f.read(bufSize)
		return s
	def seekRaw(self, offset, whence):
		r = self.f.seek(offset, whence)
		return self.f.tell()

import sys, os

if len(sys.argv) == 2:
	filename = sys.argv[1]
else:
	files = [
		"~/Music/Classic/Glenn Gould Plays Bach/Two- & Three-Part Inventions - Gould/19 Bach - Invention 13 in a (BWV 784).mp3",
		"~/Music/Rock/Tool/Lateralus/09 Lateralus.flac",
		"~/Music/Cults - Cults 7/Cults - Cults 7- - 03 The Curse.flac",
		"~/Music/Special/zorba/(01) - Theme From Zorba The Greek.ogg",
		"~/Music/Classic/Glenn Gould Plays Bach/French Suites, BWV812-7 - Gould/Bach, French Suite 5 in G, BWV816 - 5 Bourree.mp3",
		"~/Music/Electronic/Von Paul Kalkbrenner - Aaron.mp3",
		"~/Music/Electronic/One Day_Reckoning Song (Wankelmut Remix) - Asaf Avidan & the Mojos.mp3",
	]
	files = map(os.path.expanduser, files)
	filename = files[5]

if len(sys.argv) >= 3:
	filename = "?"
	duration = int(sys.argv[1])
	fingerprint = sys.argv[2]
else:
	assert os.path.isfile(filename)
	import ffmpeg
	duration, fingerprint = ffmpeg.calcAcoustIdFingerprint(Song(filename))

print "fingerprint for", os.path.basename(filename), "is:", duration, fingerprint


# AcoustID service
# see: http://acoustid.org/webservice

api_url = "http://api.acoustid.org/v2/lookup"
# "8XaBELgH" is the one from the web example from AcoustID.
# "cSpUJKpD" is from the example from pyacoustid
# get an own one here: http://acoustid.org/api-key
client_api_key = "cSpUJKpD"

params = {
	'format': 'json',
	'client': client_api_key,
	'duration': int(duration),
	'fingerprint': fingerprint,
	'meta': 'recordings recordingids releasegroups releases tracks compress',
}

import urllib
body = urllib.urlencode(params)

import urllib2
req = urllib2.Request(api_url, body)

import contextlib
with contextlib.closing(urllib2.urlopen(req)) as f:
	data = f.read()
	headers = f.info()

import json
data = json.loads(data)

from pprint import pprint
pprint(data)

#url = "http://musicbrainz.org/recording/%s"
#import webbrowser
#webbrowser.open(songurl)
