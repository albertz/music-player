#!/usr/bin/python

#  build-copyScript.py
#  MusicPlayer
#
#  Created by Albert Zeyer on 21.08.12.
#  Copyright (c) 2012 Albert Zeyer. All rights reserved.

import sys, os, shutil
from subprocess import Popen, PIPE
from glob import glob
import re
from pprint import pprint
env = os.environ
cp = shutil.copyfile

# debugging:
if False:
	pprint(env)
	pprint(sys.argv)
	sys.exit(1)

if sys.argv[1:2] == ["-qmake"]:
	qmakeVars = {}
	for arg in sys.argv[2:]:
		varname, varvalue = arg.split("=", 1)
		qmakeVars[varname] = varvalue
	# Build up Xcode compatible vars which we use here.
	env["PROJECT_DIR"] = os.path.abspath(qmakeVars["top_srcdir"] + "/mac")
	env["BUILT_PRODUCTS_DIR"] = qmakeVars["top_builddir"]
	env["TARGET_BUILD_DIR"] = qmakeVars["top_builddir"]
	env["TARGET_NAME"] = qmakeVars["TARGET"]
	env["WRAPPER_SUFFIX"] = ".app"
	env["CONTENTS_FOLDER_PATH"] = env["TARGET_NAME"] + env["WRAPPER_SUFFIX"] + "/Contents"
	env["UNLOCALIZED_RESOURCES_FOLDER_PATH"] = env["CONTENTS_FOLDER_PATH"] + "/Resources"
	env["EXECUTABLE_FOLDER_PATH"] = env["CONTENTS_FOLDER_PATH"] + "/MacOS"
	
import sys, time
sys.path += [env["PROJECT_DIR"] + "/.."]
import better_exchook
better_exchook.install()

pylibs = ["musicplayer.so", "faulthandler.so", "debugger.so", "_gui.so", "_guiCocoa.so"]
for l in pylibs:
	assert os.path.exists(env["BUILT_PRODUCTS_DIR"] + "/" + l)

# $PROJECT_DIR : /Users/az/Programmierung/music-player/mac
# $EXECUTABLE_FOLDER_PATH : MusicPlayer.app/Contents/MacOS
# $CONTENTS_FOLDER_PATH : MusicPlayer.app/Contents

# copy all Python stuff

PYDIR = env["TARGET_BUILD_DIR"] + "/" + env["UNLOCALIZED_RESOURCES_FOLDER_PATH"] + "/Python"
try: os.makedirs(PYDIR)
except OSError: pass

open(PYDIR + "/appinfo_build.py", "w").write(
	"buildTime = %r\n" % time.strftime("%Y-%m-%d %H:%M:%S +0000", time.gmtime()) +
	"gitRef = %r\n" % open(env["PROJECT_DIR"] + "/../.git/refs/heads/master").read().strip()
)

for f in pylibs:
	cp(env["BUILT_PRODUCTS_DIR"] + "/" + f, PYDIR + "/" + f)
for f in ("License.txt", "DevelopmentNotes.md", "WhatIsAMusicPlayer.md"):
	cp(env["PROJECT_DIR"] + "/../" + f, PYDIR + "/" + f)
for f in glob(env["PROJECT_DIR"] + "/../*.py"):
	cp(f, PYDIR + "/" + os.path.basename(f))
for d in ["lastfm", "tools"]:
	if os.path.exists(PYDIR + "/" + d):
		shutil.rmtree(PYDIR + "/" + d)
	shutil.copytree(env["PROJECT_DIR"] + "/../" + d, PYDIR + "/" + d, symlinks=False)


# PyObjC
for d in ["objc", "PyObjCTools"]:
	if os.path.exists(PYDIR + "/" + d):
		shutil.rmtree(PYDIR + "/" + d)
	shutil.copytree(env["PROJECT_DIR"] + "/pyobjc-core/Lib/" + d, PYDIR + "/" + d, symlinks=False)
assert os.path.exists(env["BUILT_PRODUCTS_DIR"] + "/_objc.so")
cp(env["BUILT_PRODUCTS_DIR"] + "/_objc.so", PYDIR + "/objc/_objc.so")

# PyObjC frameworks
#PyObjCDir = env["BUILT_PRODUCTS_DIR"] + "/pyobjc"
PyObjCDir = env["PROJECT_DIR"] + "/build/Release/pyobjc"
for d in glob(PyObjCDir + "/*"):
	fulldir = d
	d = os.path.basename(fulldir)
	if os.path.exists(PYDIR + "/" + d):
		shutil.rmtree(PYDIR + "/" + d)
	shutil.copytree(fulldir, PYDIR + "/" + d, symlinks=False)

# copy all dylibs

#DYLIBDIR="$TARGET_BUILD_DIR/$EXECUTABLE_FOLDER_PATH"
DYLIBDIR=PYDIR # we target ffmpeg.so, just put them into the same dir
try: os.makedirs(DYLIBDIR)
except OSError: pass

def systemRun(cmd):
	print cmd
	Popen(cmd).wait()

externalPath = os.path.normpath(env["PROJECT_DIR"] + "/../core/external")

def fixBin(binPath, targetDylibDir, installNameToolTargetDir, badPaths = ["/usr/local/","/opt/", externalPath], stripVersion = True):
	binDir = os.path.dirname(binPath)
	targetDylibDirFull = binDir + "/" + targetDylibDir

	systemRun(["install_name_tool", "-id", installNameToolTargetDir + "/" + os.path.basename(binPath), binPath])

	otoolOut = Popen(["otool","-L",binPath],stdout=PIPE).stdout.readlines()
	otoolOut = otoolOut[2:] # ignore first two lines
	for l in otoolOut:
		f = re.match("^\s+([\w/.-@]+)", l).groups()[0]
		fbase = os.path.basename(f)

		if f.startswith("@"): # e.g. "@executable_path/..."
			# probably already fixed
			continue

		if not f.startswith("/"): # strange case
			# some custom handling for now, not sure ...
			# e.g. f == "libz.so.1.2.8"
			assert f.startswith("libz.so.1.") # only this case now
			fbase = "libz.1.dylib"
			assert os.path.exists("/usr/lib/" + fbase)
			systemRun(["install_name_tool", "-change", f, "/usr/lib/" + fbase, binPath])
			continue

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
		
fixBin(PYDIR + "/musicplayer.so", ".", "@executable_path/../Resources/Python")

# When we run the MusicPlayer within Xcode, it sets the DYLD_LIBRARY_PATH to env["BUILT_PRODUCTS_DIR"]
# and it might load the musicplayer.so from there. Thus, we need to fix that one also.
fixBin(env["BUILT_PRODUCTS_DIR"] + "/musicplayer.so", ".", "@executable_path/../Resources/Python")
