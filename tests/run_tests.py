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

for fn in glob("../*.cpp"):
	c.cc([fn], options=[])
	binfile = c.get_cc_outfilename(fn) + ".bin"
	link_exec(
		binfile,
		[c.get_cc_outfilename(fn)],
		options=[]
	)
	sysExec(["./" + binfile])
