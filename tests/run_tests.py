#!/usr/bin/env python

import os, sys
from glob import glob
os.chdir(os.path.dirname(__file__))
sys.path += [".."]

import compile_utils as c

for fn in glob("*.cpp"):
	c.cc(fn)

