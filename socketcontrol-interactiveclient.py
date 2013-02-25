# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import binstruct
import socket
import appinfo
import tempfile
from glob import glob

import better_exchook
better_exchook.install()

tmpdir = tempfile.gettempdir()
files = glob("%s/%s-*-socketcontrol" % (tmpdir, appinfo.appid))
assert files
sockfile = files[0]

s = socket.socket(socket.AF_UNIX)
s.connect(sockfile)
s.setblocking(True)
f = s.makefile()

serverappid,servername,serverver = binstruct.read(f)
print "connected to", serverappid, servername, serverver
assert serverappid == appinfo.appid
assert serverver == 0.1

binstruct.write(f, (appinfo.appid, "SocketControl-InteractiveClient", 0.1, "ok"))

try: import readline
except ImportError: pass # ignore

idx = 0
while True:
	s = raw_input("> ")
	f.write(binstruct.varEncode((idx, s)).tostring())
	f.flush()
	
	answeridx,answertype,answerret = binstruct.varDecode(f)
	assert answeridx == idx
	if answertype == "compile-exception":
		print("%s in %r" % (answerret, s))
	elif answertype == "eval-exception":
		print("Exception %s" % answerret)
	elif answertype == "return":
		if answerret is not None:
			print(repr(answerret))
	else:
		assert False, "%s unknown" % answertype
