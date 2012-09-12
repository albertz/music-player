#!/usr/bin/python

import os, sys
from glob import glob
os.chdir(os.path.dirname(__file__))

def sysExec(cmd):
    print " ".join(cmd)
    r = os.system(" ".join(cmd))
    if r != 0: sys.exit(r)

sysExec(["mkdir","-p","build"])
os.chdir("build")

sysExec(["gcc", "-c"] +
	["../ffmpeg.c"] +
	glob("../chromaprint/*.cpp") +
	[
	"-DHAVE_CONFIG_H",
	"-I", "/System/Library/Frameworks/Python.framework/Headers/",
	"-I", "../chromaprint",
	"-g",
	])

sysExec(["libtool", "-dynamic", "-o", "../ffmpeg.so"] +
	glob("*.o") +
	[
	"-framework", "Python",
	"-lavformat", "-lavutil", "-lavcodec", "-lswresample", "-lportaudio",
	"-lc", "-lstdc++",
	])
