#!/usr/bin/env python

import os, sys
from glob import glob
os.chdir(os.path.dirname(__file__))

sys.path += [".."]

from compile_utils import *
import compile_utils as c

sysExec(["mkdir","-p","build"])
os.chdir("build")

c.CFLAGS += ["-I../.."]

def testCpp(fn):
	c.cc([fn], options=["-g"])
	binfile = c.get_cc_outfilename(fn) + ".bin"
	link_exec(
		binfile,
		[c.get_cc_outfilename(fn)],
		options=["-g"]
	)
	sysExec(["./" + binfile])
	print os.path.basename(fn), ": success"

def test(fn):
	if os.path.splitext(fn)[1] == ".cpp":
		testCpp(fn)
	else:
		# TODO ...
		testCpp(fn)

if __name__ == "__main__":

	if len(sys.argv) > 1:
		for fn in sys.argv[1:]:
			fn = "../" + os.path.basename(fn)
			test(fn)

	else:
		for fn in glob("../*.cpp"):
			testCpp(fn)

