# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import sys, os
import appinfo
import utils
import binstruct


def handleConnection(conn):
	conn.setblocking(True)
	f = conn.makefile()

	binstruct.write(f, (appinfo.appid, "SocketControl", 0.1))
	f.flush()
	try:
		clientappid,clientname,clientver,clientstatus = binstruct.read(f)
	except binstruct.FormatError:
		print "socketcontrol.handleConnection: wrong signature"
		return	
	if clientstatus != "ok":
		print "socketcontrol.handleConnection: status returned %s" % status
		return
	
	from State import state
	from queue import queue
	shellGlobals = {
		"state": state,
		"queue": queue,
		}
	globals = locals = shellGlobals
	COMPILE_STRING_FN = "<socketcontrol input>"
		
	while True:
		try:
			idx,s = binstruct.varDecode(f)
		except Exception:
			# probably closed
			return
		assert isinstance(s, (str,unicode))
		
		try:
			c = utils.interactive_py_compile(s, COMPILE_STRING_FN)
		except Exception as e:
			answer = (idx, "compile-exception", (e.__class__.__name__, str(e)))
		else:
			try:
				ret = eval(c, globals, locals)
			except Exception as e:
				answer = (idx, "eval-exception", (e.__class__.__name__, str(e)))
			else:
				if ret is not None:
					try:
						ret = repr(ret)
					except Exception as e:
						ret = "<repr exception: %s: %s>" % (e.__class__.__name__, str(e))
				answer = (idx, "return", ret)
		
		f.write(binstruct.varEncode(answer).tostring())
		f.flush()
		
def socketcontrolMain():	
	import tempfile
	tmpdir = tempfile.gettempdir() or "/tmp"
	global sockfilename
	sockfilename = "%s/%s-%i-socketcontrol" % (tmpdir, appinfo.appid, os.getpid())
	
	import socket
	s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	s.bind(sockfilename)
	os.chmod(sockfilename, 0700)
	s.listen(1)
		
	def listenThread():
		print "socketcontrol: listening on", sockfilename
	
		while True:
			conn, address = s.accept()
			print "socketcontrol: accepted", address
			utils.daemonThreadCall(lambda: handleConnection(conn), name="socketcontrol.handleConnection")
		
	utils.daemonThreadCall(listenThread, name="socketcontrol.listen")
	
	from State import state
	for ev,args,kwargs in state.updates.read():
		pass
	
	try: s.shutdown(socket.SHUT_RDWR)
	except Exception: pass
	try: s.close()
	except Exception: pass

