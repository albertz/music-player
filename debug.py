# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# This is the debug module: tools to debug MusicPlayer.
# This is mostly for debugging at runtime.
# - memory profiling. searching for mem-leaks
# - runtime profiling. searching slow code paths
# - other bugs

# Use socketcontrol-interactiveclient.py for interactively control.
# After being connected, just run `import debug` and use the functions from here.

import sys, os
import utils

def getDevelPath():
	def check(path):
		path = os.path.expanduser(path)
		if not os.path.isdir(path): return None
		if not os.path.isdir(path + "/.git"): return None
		return path
	for path in [
		# send me a request to include your custom dir.
		# if it isn't too unusual, i might add it here.
		"~/Programmierung/music-player",
		"~/Projects/music-player",
		"~/Coding/music-player",
	]:
		path = check(path)
		if path: return path
	return None

def addDevelSysPath():
	"adds your MusicPlayer development directory to sys.path"
	path = getDevelPath()
	assert path, "devel path not found"
	sys.path = [path] + sys.path

def iterEggPaths():
	from glob import glob
	versionStr = ".".join(map(str, sys.version_info[0:2]))
	for path in [
		sys.prefix, # = /System/Library/Frameworks/Python.framework/Versions/..
		# mac specific. you might want to make that more generic.
		"/Library/Python/%s/site-packages" % versionStr,
	]:
		for egg in glob(path + "/*.egg"):
			yield egg

def addEggPaths():
	for egg in iterEggPaths():
		if egg not in sys.path:
			sys.path += [egg]


# Profiling run traces.
# sys.{setprofile/settrace} is not really a good fit in multi-threading envs.
# There is [yappi](https://code.google.com/p/yappi/).

class ProfileCtx:
	def __enter__(self,*args):
		import yappi
		yappi.start()
	def __exit__(self,*args):
		import yappi
		yappi.stop()
		yappi.print_stats()
		yappi.clear_stats()
		
def profile(func):
	with ProfileCtx():
		func()

def createCocoaKeyEvent(keyCode, down=True):
	from AppKit import NSEvent, NSApplication, NSKeyDown, NSKeyUp, NSDate
	modifierFlags = 0
	return NSEvent.keyEventWithType_location_modifierFlags_timestamp_windowNumber_context_characters_charactersIgnoringModifiers_isARepeat_keyCode_(
		NSKeyDown if down else NSKeyUp, (0, 0), modifierFlags,
		NSDate.timeIntervalSinceReferenceDate(), #theEvent.timestamp(),
		0, #theEvent.windowNumber(),
		None, # context
		None, # characters
		None, # charactersIgnoringModifiers
		False, # isARepeat
		keyCode # keyCode
	)
	
def testCocoaPlaylistUpDown():
	# keyCode: 125 - down / 126 - up
	obj = cocoaGetPlaylistObj()
	utils.do_in_mainthread(lambda: obj.keyDown_(createCocoaKeyEvent(125,True)), wait=True)
	utils.do_in_mainthread(lambda: obj.keyDown_(createCocoaKeyEvent(126,True)), wait=True)

def cocoaGetPlaylistObj():
	import guiCocoa
	w = guiCocoa.windows["mainWindow"]
	q = w.childs["queue"]	
	ql = q.childs["queue"]
	return ql.nativeGuiObject


def dump10Secs():
	from State import state
	player = state.player

	fmtTagStr,bitsPerSample = getattr(player, "outSampleFormat", ("int",16))
	bytesPerSample = bitsPerSample / 8

	def write_wavheader(stream, datalen):
		# http://www-mmsp.ece.mcgill.ca/Documents/AudioFormats/WAVE/WAVE.html
		from struct import pack
	
		numSamples = datalen / bytesPerSample
		
		assert bitsPerSample in [8,16,24,32]
		if fmtTagStr == "int":
			fmttag = 1 # PCM format. integers
			fmtchunksize = 16 # for PCM
			needExtendedSection = False
			needFactChunk = False
		elif fmtTagStr == "float":
			# IEEE format has always extended section (which is empty), thus 18 bytes long
			fmttag = 3 # IEEE float
			fmtchunksize = 18
			needExtendedSection = True
			needFactChunk = True
			factchunksize = 4

		#wavechunksize = 36 + datalen # PCM
		wavechunksize = 20 + fmtchunksize + datalen
		if needFactChunk:
			wavechunksize += factchunksize + 8

		stream.write(pack("<4sI4s", "RIFF", wavechunksize, "WAVE"))
	
		stream.write("fmt ")
		stream.write(pack("<L", fmtchunksize))
		stream.write(pack("<H", fmttag))
		
		numChannels = player.outNumChannels
		samplerate = player.outSamplerate
		byteRate = samplerate * numChannels * bytesPerSample
		blockAlign = numChannels * bytesPerSample
		stream.write(pack("<H", numChannels))
		stream.write(pack("<L", samplerate))
		stream.write(pack("<L", byteRate))
		stream.write(pack("<H", blockAlign))
		stream.write(pack("<H", bitsPerSample))
		if needExtendedSection:
			stream.write(pack("<H", 0)) # size of extended section
		
		if needFactChunk:
			stream.write("fact")
			stream.write(pack("<L", factchunksize))
			stream.write(pack("<L", numChannels * numSamples))		
		
		stream.write("data")
		stream.write(pack("<L", datalen))
	
	player.playing = False
	player.soundcardOutputEnabled = False
	player.playing = True
	
	wholebuf = ""
	# read up to 10 secs
	while len(wholebuf) < player.outNumChannels * player.outSamplerate * bytesPerSample * 10:
		wholebuf += player.readOutStream(player.outNumChannels * player.outSamplerate)

	player.playing = False
	player.soundcardOutputEnabled = True

	import appinfo
	wavfn = appinfo.userdir + "/debugdump.wav"
	f = open(wavfn, "w")
	write_wavheader(f, len(wholebuf))
	f.write(wholebuf)
	f.close()
	
	return wavfn
