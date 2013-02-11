# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

try:
	import argparse
	argParser = argparse.ArgumentParser()
except ImportError:
	print "Error, argparse not available. This needs Python >=2.7."
	# Dummy fallback
	class DummyArgParser:
		def add_argument(self, key, **kwargs):
			assert key[0:2] == "--"
			setattr(self, key[2:], False)
		def parse_args(self): return self
	argParser = DummyArgParser()

argParser.add_argument(
	"--shell", action="store_true",
	help="uses a Python shell instead of the standard stdin control")
argParser.add_argument(
	"--qtgui", action="store_true",
	help="force Qt GUI")
argParser.add_argument(
	"--forkExecProc", nargs=2)
