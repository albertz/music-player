
import sys, os, gc

def step():
	gc.collect()
	os.system("ps axu %i" % os.getpid())
	print "\npress enter to continue"
	sys.stdin.readline()

def progr():
	sys.stdout.write(".")
	sys.stdout.flush()

from RandomFileQueue import RandomFileQueue
fileQueue = RandomFileQueue(
	rootdir=os.path.expanduser("~/Music"),
	fileexts=["mp3", "ogg", "flac", "wma"])


import ffmpeg
print "imported"
step()

N = 10

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

for i in xrange(N):
	ffmpeg.calcBitmapThumbnail(Song(fileQueue.getNextFile()))
	progr()

print "after calcBitmapThumbnail"
step()

for i in xrange(N):
	ffmpeg.getMetadata(Song(fileQueue.getNextFile()))
	progr()

print "after getMetadata"
step()

