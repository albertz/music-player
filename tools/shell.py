# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import sys, os
importPath = os.path.join(os.path.dirname(__file__), "..")
if importPath not in sys.path:
	sys.path += [importPath]

import better_exchook
if __name__ == "__main__":
	better_exchook.install()

import binstruct
import socket
import appinfo
import tempfile
from glob import glob

def connect():
	global f, s
	s = socket.socket(socket.AF_UNIX)

	sockfile = None
	if __name__ == "__main__":
		if len(sys.argv) > 1:
			sockfile = sys.argv[1]
			assert os.path.exists(sockfile)

			s.connect(sockfile)

	if not sockfile:
		tmpdir = tempfile.gettempdir()
		files = glob("%s/%s-*-socketcontrol" % (tmpdir, appinfo.appid))
		assert files, "no socket files found"

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


def latestPyStatement(execStr):
	tokens = list(better_exchook.parse_py_statement(execStr))
	bracketDepth = 0
	s = ""
	def tokenToStr(ttype,tstr):
		if ttype in ["op","id"]: return tstr
		if ttype == "str": return repr(tstr)
		assert False, "tokenToStr(%r, %r)" % (ttype, tstr)
	for i,(ttype,tstr) in reversed(enumerate(tokens)):
		if bracketDepth > 1:
			if ttype == "op" and tstr in "({[":
				bracketDepth -= 1
			s = tokenToStr(ttype,tstr) + s
			continue
		if ttype == "op" and tstr in "]})":
			bracketDepth += 1
			s = tokenToStr(ttype,tstr) + s
			continue
		if (ttype,tstr) == ("op",".") or ttype in ["id","str"]:
			s = tokenToStr(ttype,tstr) + s
			continue
		break
	return s

idx = 0
def _remoteExec(execStr):
	global f, idx
	idx += 1
	f.write(binstruct.varEncode((idx, s)).tostring())
	f.flush()

	answeridx,answertype,answerret = binstruct.varDecode(f)
	assert answeridx == idx
	return answertype, answerret

def remoteExec(execStr):
	answertype, answerret = _remoteExec(s)
	if answertype == "return":
		return answerret
	assert answertype in ["compile-exception", "eval-exception"]
	raise Exception, "%s : %s" % (answerret[0], answerret[1])

if __name__ == "__main__":

	try:
		import readline

		histfile = appinfo.userdir + "/shell.history"
		try: readline.read_history_file(histfile)
		except IOError: pass

		import atexit
		atexit.register(readline.write_history_file, histfile)

		readline.parse_and_bind('tab: complete')

		commands = ["foo", "bar", "buz"]
		def completer(text, state):
			options = [i for i in commands if i.startswith(text)]
			if state < len(options):
				return options[state]
			else:
				return None
		readline.set_completer(completer)

	except ImportError: pass # ignore

	connect()

	while True:
		try: s = raw_input("> ")
		except (KeyboardInterrupt,EOFError):
			print("")
			sys.exit(0)
		if s.strip() == "": continue

		answertype, answerret = _remoteExec(s)
		if answertype == "compile-exception":
			print("%s : %s in %r" % (answerret[0], answerret[1], s))
		elif answertype == "eval-exception":
			print("Exception %s : %s" % (answerret[0], answerret[1]))
		elif answertype == "return":
			if answerret is not None:
				print(answerret)
		else:
			assert False, "%s unknown" % answertype
