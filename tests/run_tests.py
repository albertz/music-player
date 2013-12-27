#!/usr/bin/env python

import os, sys
from glob import glob
os.chdir(os.path.dirname(__file__))

def compileCpp(fn):
	pass

for fn in glob("*.cpp"):
	compileCpp(fn)

