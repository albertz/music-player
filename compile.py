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

def includeExists(fn):
	for p in ["/usr/include", "/usr/local/include"]:
		if os.path.exists(p + "/" + fn): return True
	return False

staticChromaprint = False
staticSwresample = False

if not includeExists("libswresample/libswresample.h"):
	print "forcing staticSwresample = True"
	staticSwresample = True

ffmpegFiles = ["../ffmpeg.c"] + \
	(glob("../chromaprint/*.cpp") if staticChromaprint else [])

if staticSwresample:
	ffmpegFiles += map(lambda fn: "../libs/libswresample/" + fn,
		[
			"audioconvert.c",
			"dither.c",
			"rematrix.c",
			"resample.c",
			"swresample.c",
		])

sysExec(["cc", "-std=c99", "-c"] + ffmpegFiles +
	[
		"-DHAVE_CONFIG_H",
		"-I", "/System/Library/Frameworks/Python.framework/Headers/",
		"-g",
	] +
	(["-I", "../chromaprint"] if staticChromaprint else []) +
	(["-I", "../libs/libswresample"] if staticSwresample else [])
)

sysExec(["libtool", "-dynamic", "-o", "../ffmpeg.so"] +
	[os.path.splitext(os.path.basename(fn))[0] + ".o" for fn in ffmpegFiles] +
	[
		"-framework", "Python",
		"-lavformat", "-lavutil", "-lavcodec", "-lswresample", "-lportaudio",
		"-lc", "-lstdc++",
	] +
	([] if staticChromaprint else ["-lchromaprint"])
)

levelDbFiles = glob("../leveldb*.cc")

sysExec(["cc", "-c"] + levelDbFiles +
	[
		"-I", "/System/Library/Frameworks/Python.framework/Headers/",
		"-g",
	]
)

sysExec(["libtool", "-dynamic", "-o", "../leveldb.so"] +
	[os.path.splitext(os.path.basename(fn))[0] + ".o" for fn in levelDbFiles] +
	[
		"-framework", "Python",
		"-lleveldb", "-lsnappy",
		"-lc", "-lstdc++",
	]
)
