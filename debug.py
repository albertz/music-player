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
	
def testCocoaKeyEvent(obj, keyCode):
	# keyCode: 125 - down / 126 - up
	# or use CGPostKeyboardEvent ?
	if not obj:
		from AppKit import NSApplication
		obj = NSApplication.sharedApplication()
	obj.postEvent_atStart_(createCocoaKeyEvent(keyCode, True), True)
	obj.postEvent_atStart_(createCocoaKeyEvent(keyCode, False), True)

def cocoaGetPlaylistObj():
	import guiCocoa
	w = guiCocoa.windows["mainWindow"]
	q = w.childs["queue"]	
	ql = q.childs["queue"]
	return ql.nativeGuiObject
