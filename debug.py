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

