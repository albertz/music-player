#!/usr/bin/env python

import os, sys
os.chdir(os.path.dirname(__file__))

# Import compile_utils from core.
sys.path += ["core"]
from compile_utils import *
import compile_utils as c
from glob import glob

# Compile core module.
sysExec(["./core/compile.py"])
sysExec(["cp", "core/musicplayer.so", "musicplayer.so"])


sysExec(["mkdir","-p","build"])
os.chdir("build/")

# Compile _gui.so.
print("* Building _gui.so")
guiFiles = glob("../_gui/*.cpp")
cc(
	guiFiles,
	["-I../core"] + get_python_ccopts()
)
link(
	"../_gui.so",
	[c.get_cc_outfilename(fn) for fn in guiFiles],
	get_python_linkopts()
)

if sys.platform == "darwin":
	# Compile _guiCocoa.so.
	print("* Building _guiCocoa.so")
	guiCocoaFiles = glob("../mac/gui/*.m*") + glob("../mac/gui/*.cpp")

	PyObjCBridgeFile = "../mac/gui/PyObjCBridge.m"
	guiCocoaFiles.remove(PyObjCBridgeFile) # we will handle that differently

	cc(
		guiCocoaFiles,
		[
			"-I../core",
			"-I../_gui",
			"-fobjc-arc",
		] +
		get_python_ccopts()
	)

	guiCocoaFiles.append(PyObjCBridgeFile)
	cc(
		[PyObjCBridgeFile],
		[
			"-I../core",
			"-I../_gui",
			"-I../mac/pyobjc-core/Modules/objc",
			"-I../mac/pyobjc-core/libffi-src/include",
		] +
		get_python_ccopts()
	)

	link(
		"../_guiCocoa.so",
		[c.get_cc_outfilename(fn) for fn in guiCocoaFiles],
		[
			"-framework", "Cocoa",
			"-framework", "Foundation",
			"-framework", "CoreFoundation",
		] +
		get_python_linkopts()
	)

