#!/usr/bin/env python

import os
import sys
import shutil
import subprocess
sys.path = ["."] + sys.path
os.chdir(os.path.dirname(__file__))

TargetDir = "build/Release/pyobjc"
try: shutil.rmtree(TargetDir)
except OSError: pass
os.mkdir(TargetDir)
assert os.path.exists(TargetDir)

if False:
	# TODO: doesnt work currently because of protocols..
	SDKROOT="/Developer/SDKs/MacOSX10.6.sdk"
	assert os.path.exists(SDKROOT)
	CFLAGS=["-mmacosx-version-min=10.6", "-DMAC_OS_X_VERSION_MIN_REQUIRED=1060", "--sysroot", SDKROOT]
	os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.6"
	os.environ["SDKROOT"] = SDKROOT
else:
	CFLAGS=["-mmacosx-version-min=10.6"]
	os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.6"

def copytree(src, dst, symlinks=False):
	try: os.makedirs(dst)
	except OSError: pass # probably exists or so
	names = os.listdir(src)
	for name in names:
		srcname = os.path.join(src, name)
		dstname = os.path.join(dst, name)
		if symlinks and os.path.islink(srcname):
			linkto = os.readlink(srcname)
			os.symlink(linkto, dstname)
		elif os.path.isdir(srcname):
			copytree(srcname, dstname, symlinks)
		else:
			# Will raise a SpecialFileError for unsupported file types
			shutil.copy2(srcname, dstname)


setup_kwargs = None
def _catch_setup(**kwargs):
	global setup_kwargs
	setup_kwargs = kwargs

for framework in ["Cocoa", "Quartz"]:
	fDir = "pyobjc-framework-" + framework

	# fork so that we can import `setup` in each dir
	pid = os.fork()
	if pid == 0:
		os.chdir(fDir)
		import pyobjc_setup
		pyobjc_setup.setup = _catch_setup

		origExtension = pyobjc_setup._Extension
		def MyExtension(*args, **kwds):
			for attr in ["extra_compile_args", "extra_link_args"]:
				flags = kwds[attr]
				idx = flags.index("-isysroot")
				flags[idx:idx+2] = []
			return origExtension(*args, **kwds)
		pyobjc_setup._Extension = MyExtension

		import setup
		assert setup_kwargs is not None

		for package in setup_kwargs["packages"]:
			print "*** package:", package
			package = package.replace(".", "/")
			copytree(
				"Lib/" + package,
				"../" + TargetDir + "/" + package)

		for extmod in setup_kwargs["ext_modules"]:
			if extmod.name.split(".")[0] == "PyObjCTest": continue # ignore

			print "*** ext module:", extmod.name
			filename = extmod.name.replace(".", "/") + ".so"
			args = \
				["cc"] + \
				extmod.sources + \
				CFLAGS + \
				["-I../../python-embedded/CPython/Include",
				 "-I../../python-embedded/pylib",
				 "-I../pyobjc-core/Modules/objc"] + \
				extmod.extra_compile_args + \
				extmod.extra_link_args + ["-undefined", "dynamic_lookup"] + \
				["-shared", "-o", "../" + TargetDir + "/" + filename]
			print " ".join(args)
			res = subprocess.call(args)
			if res != 0: sys.exit(res)

		sys.exit(0)

	else:
		_, res = os.waitpid(pid, 0)
		if res != 0: sys.exit(res)
