#!/usr/bin/python

#  build-copyScript.py
#  MusicPlayer
#
#  Created by Albert Zeyer on 21.08.12.
#  Copyright (c) 2012 Albert Zeyer. All rights reserved.

import os, shutil
from subprocess import Popen, PIPE
from glob import glob
import re
env = os.environ
cp = shutil.copyfile

import sys
sys.path += [env["PROJECT_DIR"] + "/.."]
import better_exchook
better_exchook.install()

assert os.path.exists(env["BUILT_PRODUCTS_DIR"] + "/ffmpeg.so")

# $PROJECT_DIR : /Users/az/Programmierung/music-player/mac
# $EXECUTABLE_FOLDER_PATH : MusicPlayer.app/Contents/MacOS
# $CONTENTS_FOLDER_PATH : MusicPlayer.app/Contents

# copy all Python stuff

PYDIR = env["TARGET_BUILD_DIR"] + "/" + env["UNLOCALIZED_RESOURCES_FOLDER_PATH"] + "/Python"
try: os.makedirs(PYDIR)
except OSError: pass

cp(env["BUILT_PRODUCTS_DIR"] + "/ffmpeg.so", PYDIR + "/ffmpeg.so")
for f in glob(env["PROJECT_DIR"] + "/../*.py"):
	cp(f, PYDIR + "/" + os.path.basename(f))
#cp "$PROJECT_DIR/"*.py "$PYDIR/"


# copy all dylibs

#DYLIBDIR="$TARGET_BUILD_DIR/$EXECUTABLE_FOLDER_PATH"
DYLIBDIR=PYDIR # we target ffmpeg.so, just put them into the same dir
try: os.makedirs(DYLIBDIR)
except OSError: pass

def fixBin(binPath, targetDylibDir, badPaths = ["/usr/local/"], stripVersion = True):
	binDir = os.path.dirname(binPath)
	targetDylibDirFull = binDir + "/" + targetDylibDir
	
	otoolOut = Popen(["otool","-L",binPath],stdout=PIPE).stdout.readlines()
	otoolOut = otoolOut[2:] # ignore first two lines
	for l in otoolOut:
		f = re.match("^\s+([\w/.-]+)", l).groups()[0]
		fbase = os.path.basename(f)
		if not [True for badPath in badPaths if f.startswith(badPath)]: continue

		if stripVersion:
			fbase = fbase.split(".")
			fbase = fbase[0] + "." + fbase[-1]
					
		print f, "->", targetDylibDir + "/" + fbase, "in", binPath
		Popen(["install_name_tool", "-change", f, targetDylibDir + "/" + fbase, binPath])

		if not os.path.exists(targetDylibDirFull + "/" + fbase):
			cp(f, targetDylibDirFull + "/" + fbase)		
			fixBin(targetDylibDirFull + "/" + fbase, targetDylibDir, badPaths, stripVersion)
		
fixBin(PYDIR + "/ffmpeg.so", ".")
