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

import sys, time
sys.path += [env["PROJECT_DIR"] + "/.."]
import better_exchook
better_exchook.install()

assert os.path.exists(env["BUILT_PRODUCTS_DIR"] + "/ffmpeg.so")
assert os.path.exists(env["BUILT_PRODUCTS_DIR"] + "/faulthandler.so")
assert os.path.exists(env["BUILT_PRODUCTS_DIR"] + "/_guiCocoaCommon.dylib")

# $PROJECT_DIR : /Users/az/Programmierung/music-player/mac
# $EXECUTABLE_FOLDER_PATH : MusicPlayer.app/Contents/MacOS
# $CONTENTS_FOLDER_PATH : MusicPlayer.app/Contents

# copy all Python stuff

PYDIR = env["TARGET_BUILD_DIR"] + "/" + env["UNLOCALIZED_RESOURCES_FOLDER_PATH"] + "/Python"
try: os.makedirs(PYDIR)
except OSError: pass

open(PYDIR + "/appinfo_build.py", "w").write(
	"buildTime = %r\n" % time.strftime("%Y-%m-%d %H:%M:%S +0000", time.gmtime())
)

for f in ("ffmpeg.so","faulthandler.so","_guiCocoaCommon.dylib"):
	cp(env["BUILT_PRODUCTS_DIR"] + "/" + f, PYDIR + "/" + f)
for f in ("License.txt", "DevelopmentNotes.md", "WhatIsAMusicPlayer.md"):
	cp(env["PROJECT_DIR"] + "/../" + f, PYDIR + "/" + f)
for f in glob(env["PROJECT_DIR"] + "/../*.py"):
	cp(f, PYDIR + "/" + os.path.basename(f))
for d in ["lastfm"]:
	if os.path.exists(PYDIR + "/" + d):
		shutil.rmtree(PYDIR + "/" + d)
	shutil.copytree(env["PROJECT_DIR"] + "/../" + d, PYDIR + "/" + d, symlinks=False)


# copy all dylibs

#DYLIBDIR="$TARGET_BUILD_DIR/$EXECUTABLE_FOLDER_PATH"
DYLIBDIR=PYDIR # we target ffmpeg.so, just put them into the same dir
try: os.makedirs(DYLIBDIR)
except OSError: pass

def systemRun(cmd):
	print cmd
	Popen(cmd).wait()

def fixBin(binPath, targetDylibDir, installNameToolTargetDir, badPaths = ["/usr/local/","/opt/"], stripVersion = True):
	binDir = os.path.dirname(binPath)
	targetDylibDirFull = binDir + "/" + targetDylibDir

	systemRun(["install_name_tool", "-id", installNameToolTargetDir + "/" + os.path.basename(binPath), binPath])

	otoolOut = Popen(["otool","-L",binPath],stdout=PIPE).stdout.readlines()
	otoolOut = otoolOut[2:] # ignore first two lines
	for l in otoolOut:
		f = re.match("^\s+([\w/.-]+)", l).groups()[0]
		fbase = os.path.basename(f)
		if not [True for badPath in badPaths if f.startswith(badPath)]: continue

		if stripVersion:
			fbase = fbase.split(".")
			fbase = fbase[0] + "." + fbase[-1]
					
		#print f, "->", targetDylibDir + "/" + fbase, "in", binPath
		systemRun(["install_name_tool", "-change", f, installNameToolTargetDir + "/" + fbase, binPath])

		if not os.path.exists(targetDylibDirFull + "/" + fbase):
			# Note: If there are errors here (file-not-found), it means that the binary links to a non-existing lib. Probably the lib has been updated. The fix usually is to update also the binary (which is probably also a lib).
			cp(f, targetDylibDirFull + "/" + fbase)		
			fixBin(targetDylibDirFull + "/" + fbase, targetDylibDir, installNameToolTargetDir, badPaths, stripVersion)
		
fixBin(PYDIR + "/ffmpeg.so", ".", "@executable_path/../Resources/Python")
