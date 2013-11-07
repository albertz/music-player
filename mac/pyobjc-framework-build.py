#!/usr/bin/env python

import os, sys
sys.path = ["."] + sys.path
os.chdir(os.path.dirname(__file__))

try: os.mkdir("build/Release/pyobjc")
except OSError: pass # probably already exists
finally: assert os.path.exists("build/Release/pyobjc")

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
		import setup
		assert setup_kwargs is not None

		print setup_kwargs
		sys.exit(0)
		
	else:
		_, res = os.waitpid(pid, 0)
		if res != 0: sys.exit(res)
