import better_exchook
better_exchook.install()

import sys, os, gc

def step():
	gc.collect()
	os.system("ps up %i" % os.getpid())
	#print "\npress enter to continue"
	#sys.stdin.readline()

def progr():
	sys.stdout.write(".")
	sys.stdout.flush()

def getFileList(n):
	from RandomFileQueue import RandomFileQueue
	fileQueue = RandomFileQueue(
		rootdir=os.path.expanduser("~/Music"),
		fileexts=["mp3", "ogg", "flac", "wma"])
	return [fileQueue.getNextFile() for i in xrange(n)]

N = 10
files = getFileList(N)
from pprint import pprint
pprint(files)

import ffmpeg
print "imported"
step()


for i in xrange(N):
	ffmpeg.createPlayer()

print "after createPlayer"
step()


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

for f in files:
	ffmpeg.getMetadata(Song(f))
	progr()

print "after getMetadata"
step()


for f in files:
	ffmpeg.calcAcoustIdFingerprint(Song(f))
	progr()

print "after calcAcoustIdFingerprint"
step()


for f in files:
	ffmpeg.calcBitmapThumbnail(Song(f))
	progr()

print "after calcBitmapThumbnail"
step()
