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

def _parsePyString(i, s):
	strType = s[i]
	assert strType in "\"\'"
	escaped = False
	finished = False
	while True:
		i += 1
		if i >= len(s): break
		if escaped:
			escaped = False
			continue
		if s[i] == "\\":
			escaped = True
		elif s[i] == strType:
			finished = True
			break
	return locals()

def _parsePyStatement(i, s):
	latestPyExpStart = i
	latestDot = None
	suggestedCompletion = None
	while True:
		if i >= len(s): break
		c = s[i]
		if c in "({[":
			state = _parsePyStatement(i+1, s)
			i = state["i"]
			if i >= len(s):
				return state
			assert s[i] in "]})"
			# we have no real context. user should put dot or so
			suggestedCompletion = ""
		elif c in "]})":
			break
		elif c in "\"\'":
			state = _parsePyString(i, s)
			i = state["i"]
			if not state["finished"]:
				assert i >= len(s)
				suggestedCompletion = ""
				if not state["escaped"]:
					suggestedCompletion = c
				break
			assert s[i] == c
			# we have no real context. user should put dot or so
			suggestedCompletion = ""
		elif c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_":
			pass
		elif c.strip() == "":
			pass
		elif c == ".":
			latestDot = i
			suggestedCompletion = None
		else: # it's an operation
			return _parsePyStatement(i + 1, s)
		i += 1
	return locals()

def _suggestPyCompletion(stmnt):
	state = _parsePyStatement(0, stmnt)
	suggestedCompletion = state["suggestedCompletion"]
	if suggestedCompletion is not None: return locals()
	if state["latestDot"] is None:
		contextStmnt = ""
		contextStart = stmnt[state["latestPyExpStart"]:]
		contextLeft = stmnt[:state["latestPyExpStart"]]
	else:
		contextStmnt = stmnt[state["latestPyExpStart"]:state["latestDot"]]
		contextStart = stmnt[state["latestDot"]+1:]
		contextLeft = stmnt[:state["latestDot"]+1]
	return locals()

def _getPyCompletions(stmnt):
	stmnt = stmnt.rstrip()
	state = _suggestPyCompletion(stmnt)
	suggestedCompletion = state["suggestedCompletion"]
	if suggestedCompletion is not None: return [stmnt + suggestedCompletion]
	contextStmnt = state["contextStmnt"]
	contextStart = state["contextStart"]
	contextStart = contextStart.lower().strip()
	contextLeft = state["contextLeft"]
	ctx = remoteExec("dir(%s)" % contextStmnt)
	assert isinstance(ctx, list)
	if contextStmnt.strip() == "":
		# Add builtins. Note that these are from us (the shell client),
		# not the server. But we just expect these to be mostly the same.
		import __builtin__
		ctx += dir(__builtin__)
	return [contextLeft + s for s in ctx if s.lower().startswith(contextStart)]

idx = 0
def _remoteExec(execStr):
	global f, idx
	idx += 1
	f.write(binstruct.varEncode((idx, execStr)).tostring())
	f.flush()

	answeridx,answertype,answerret = binstruct.varDecode(f)
	assert answeridx == idx
	return answertype, answerret

def remoteExec(execStr, evalCtx=None):
	answertype, answerret = _remoteExec(execStr)
	if answertype == "return":
		return eval(answerret, evalCtx)
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

		def completer(text, state):
			try:
				options = _getPyCompletions(text)
			except Exception as e:
				print e
				return None
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
