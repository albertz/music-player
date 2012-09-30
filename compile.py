#!/usr/bin/python

import os, sys
from glob import glob
os.chdir(os.path.dirname(__file__))

def sysExec(cmd):
    print " ".join(cmd)
    r = os.system(" ".join(cmd))
    if r != 0: sys.exit(r)

def link(outfile, infiles, options):
	if sys.platform == "darwin":
		sysExec(
			["libtool", "-dynamic", "-o", outfile] +
			infiles +
			options + 
			["-lc", "-lstdc++"]
		)
	else:
		sysExec(
			["ld", "-shared", "-o", outfile] +
			["-L/usr/local/lib"] +
			options +
			infiles +
			["-lc"]
		)

CFLAGS = os.environ.get("CFLAGS", "").split()

def cc(files, options):
	sysExec(["cc"] + options + CFLAGS + ["-c"] + files)

sysExec(["mkdir","-p","build"])
os.chdir("build")

staticChromaprint = False

ffmpegFiles = ["../ffmpeg.c"] + \
	(glob("../chromaprint/*.cpp") if staticChromaprint else [])

cc(
	ffmpegFiles,
	[
		"-std=c99",
		"-DHAVE_CONFIG_H",
		"-I", "/System/Library/Frameworks/Python.framework/Headers/", # mac
		"-I", "/usr/include/python2.7", # common linux/unix
		"-g",
	] +
	(["-I", "../chromaprint"] if staticChromaprint else [])
)

link(
	"../ffmpeg.so",
	[os.path.splitext(os.path.basename(fn))[0] + ".o" for fn in ffmpegFiles],
	(["-framework","Python"] if sys.platform == "darwin" else ["-lpython2.7"]) +
	[
		"-lavutil",
		"-lavformat",
		"-lavcodec",
		"-lswresample",
		"-lportaudio",
	] +
	([] if staticChromaprint else ["-lchromaprint"])
)

levelDbFiles = glob("../leveldb*.cc")

cc(
	levelDbFiles,
	[
		"-I", "/System/Library/Frameworks/Python.framework/Headers/", # mac
		"-I", "/usr/include/python2.7", # common linux/unix
		"-g",
	]
)

link(
	"../leveldb.so",
	[os.path.splitext(os.path.basename(fn))[0] + ".o" for fn in levelDbFiles],
	(["-framework","Python"] if sys.platform == "darwin" else ["-lpython2.7"]) +
	[
		"-lleveldb", "-lsnappy",
	]
)
