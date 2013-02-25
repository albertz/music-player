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
	clientappid,clientname,clientver,status = binstruct.read(f)
	assert status == "ok"
	
	from State import state
	from queue import queue
	shellGlobals = {
		"state": state,
		"queue": queue,
		}
	globals = locals = shellGlobals
	
	while True:
		idx,s = binstruct.varDecode(f)
		assert isinstance(s, (str,unicode))
		
		try:
			c = compile(s, COMPILE_STRING_FN, "single")
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
						ret = str(ret)
					except Exception as e:
						ret = "<str-cast exception: %s: %s>" % (e.__class__.__name__, str(e))
				answer = (idx, "return", ret)
		
		f.write(binstruct.varEncode(answer).tostring())

def socketcontrolMain():	
	import tempfile
	tmpdir = tempfile.gettempdir() or "/tmp"
	sockfilename = "%s/%s-%i-socketcontrol" % (tmpdir, appinfo.appid, os.getpid())
	
	import socket
	s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	s.bind(sockfilename)
	s.listen(1)
	#s.settimeout(1)
		
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
	
	s.shutdown(socket.SHUT_RDWR)
	s.close()
	