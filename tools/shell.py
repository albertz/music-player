# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import sys, os
sys.path += [os.path.dirname(__file__) + "/.."]

import better_exchook
better_exchook.install()

import binstruct
import socket
import appinfo
import tempfile
from glob import glob

s = socket.socket(socket.AF_UNIX)

import os,sys
if len(sys.argv) > 1:
	sockfile = sys.argv[1]
	assert os.path.exists(sockfile)

	s.connect(sockfile)

else:
	tmpdir = tempfile.gettempdir()
	files = glob("%s/%s-*-socketcontrol" % (tmpdir, appinfo.appid))
	assert files
	
	for fn in files:
		sockfile = fn
		try:
			s.connect(sockfile)
		except socket.error:
			pass
		else:
			print "socket:", sockfile
			break
	assert s
	
s.setblocking(True)
f = s.makefile()

serverappid,servername,serverver = binstruct.read(f)
print "connected to", serverappid, servername, serverver
assert serverappid == appinfo.appid
assert serverver == 0.1

binstruct.write(f, (appinfo.appid, "SocketControl-InteractiveClient", 0.1, "ok"))
f.flush()

try: import readline
except ImportError: pass # ignore

idx = 0
while True:
	idx += 1
	try: s = raw_input("> ")
	except (KeyboardInterrupt,EOFError):
		print("")
		sys.exit(0)
	
	if s.strip() == "": continue
	f.write(binstruct.varEncode((idx, s)).tostring())
	f.flush()
	
	answeridx,answertype,answerret = binstruct.varDecode(f)
	assert answeridx == idx
	if answertype == "compile-exception":
		print("%s : %s in %r" % (answerret[0], answerret[1], s))
	elif answertype == "eval-exception":
		print("Exception %s : %s" % (answerret[0], answerret[1]))
	elif answertype == "return":
		if answerret is not None:
			print(answerret)
	else:
		assert False, "%s unknown" % answertype
