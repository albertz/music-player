# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# This is an implementation of the [MPD protocol](http://www.musicpd.org/doc/protocol/).

import utils

def handleConnection(conn, addr):
	print "mpdBackend: accepted", addr

	conn.setblocking(True)
	f = conn.makefile()

	while not f.closed:
		l = f.read(1)
		if l == "": break
		print "mpd conn:", repr(l)

	conn.close()
	print "mpdBackend: closed", addr

def listenThread(s):
	import socket
	while s:
		try: conn, addr = s.accept()
		except socket.timeout: continue
		except socket.error: break
		utils.daemonThreadCall(handleConnection, args=(conn, addr), name="mpdBackend.handleConnection")
		conn, addr = None, None # remove refs here

def mpdBackendMain():
	import appinfo
	host = appinfo.config.mpdHost
	port = appinfo.config.mpdPort
	
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
	s.bind((host,port))
	s.listen(1)
	s.settimeout(0.1)
	print "mpdBackend listening on %s:%i" % (host,port)

	t = utils.daemonThreadCall(listenThread, args=(s,), name="mpdBackend.listen")
	
	# wait for exit
	from State import state
	for ev,args,kwargs in state.updates.read():
		pass
	
	s.close()	
	t.join()
