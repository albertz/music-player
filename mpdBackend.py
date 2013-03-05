# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# This is an implementation of the [MPD protocol](http://www.musicpd.org/doc/protocol/).

MpdVersion = "0.17.0"

import utils, time, State
state = State.state

ACK_ERROR_NOT_LIST = 1
ACK_ERROR_ARG = 2
ACK_ERROR_PASSWORD = 3
ACK_ERROR_PERMISSION = 4
ACK_ERROR_UNKNOWN = 5
ACK_ERROR_NO_EXIST = 50
ACK_ERROR_PLAYLIST_MAX = 51
ACK_ERROR_SYSTEM = 52
ACK_ERROR_PLAYLIST_LOAD = 53
ACK_ERROR_UPDATE_ALREADY = 54
ACK_ERROR_PLAYER_SYNC = 55
ACK_ERROR_EXIST = 56

class MpdException(Exception):
	def __init__(self, errNum=ACK_ERROR_SYSTEM, msg=""):
		self.errNum = errNum
		self.msg = msg

class Session:
	def __init__(self, f):
		self.f = f
		self.Commands = {}
		from types import MethodType
		for fname in dir(self):
			f = getattr(self, fname)
			if not isinstance(f, MethodType): continue
			if fname[:3] != "cmd": continue
			cmdName = fname[3:].lower()
			self.Commands[cmdName] = f

	def cmdCommands(self):
		f = self.f
		f.write("commands\n")
		for cmdName in self.Commands.keys():
			f.write("command: %s\n" % cmdName)
	
	def cmdNotCommands(self):
		pass # nothing
	
	def cmdStatus(self):
		# see mpd_getStatus in https://github.com/TheStalwart/Theremin/blob/master/libmpdclient-0.18.96/src/libmpdclient.c
		f = self.f
		if state.player.playing:
			f.write("state: play\n")
		else:
			f.write("state: pause\n")
		f.write("playlist: 0\n")
		f.write("playlistlength: %i\n" % (len(state.queue.queue.list) + 1))
		f.write("volume: -1\n") # whatever that means
		f.write("song: 0\n")
		f.write("songid: 0\n")
		f.write("nextsong: 1\n")
		f.write("nextsongid: 1\n")
		f.write("time: %i:%03i\n" % (state.player.curSongPos, state.player.curSongPos % 1000))
		f.write("elapsed: %f\n" % state.player.curSongPos)
		
	def cmdOutputs(self):
		f = self.f
		f.write("outputs\n")
		f.write("outputid: 0\n")
		f.write("outputname: default detected output\n")
		f.write("outputenabled: 1\n")
	
	def cmdStats(self):
		# some fake stats to keep the clients happy
		f = self.f
		f.write("artists: 2064\n")
		f.write("albums: 1621\n")
		f.write("songs: 12461\n")
		f.write("uptime: %i\n" % (time.time() - 1362508783))
		f.write("playtime: 100\n")
		f.write("db_playtime: 3266651\n")
		f.write("db_update: %i\n" % time.time())
	
	def cmdListAllInfo(f, dir):
		pass
	
	def cmdLsInfo(f, dir):
		pass
	
	def cmdPlay(f, *args):
		state.player.playing = True
	
	def cmdPlayId(f, playid):
		state.player.playing = True
	
	def cmdPause(f, *args):
		state.player.playing = False
	
	def cmdStop(f, *args):
		state.player.playing = False
	
	def cmdNext(f):
		state.player.nextSong()
	
	def cmdPrevious(f):
		pass
	
	def dumpSong(self, songid, song):
		f = self.f
		f.write("file: %s\n" % getattr(song, "url", "").encode("utf8"))
		f.write("Artist: %s\n" % getattr(song, "artist", "<unknown>").encode("utf8"))
		f.write("Title: %s\n" % getattr(song, "title", "<unknown>").encode("utf8"))
		f.write("Time: %i\n" % getattr(song, "duration", 0))
		f.write("Pos: %i\n" % songid)
		f.write("Id: %i\n" % songid)
	
	def cmdPlaylistId(self, listid):
		listid = int(listid)
		if listid == 0:
			song = state.curSong
		else:
			assert listid > 0
			try:
				song = state.queue.queue.list[listid - 1]
			except IndexError:
				raise MpdException(errNum=ACK_ERROR_NO_EXIST, msg="No such song")
		self.dumpSong(listid, song)
	
	def cmdPlChanges(self, version):
		self.dumpSong(0, state.curSong)
		for idx,song in enumerate(list(state.queue.queue.list)):
			self.dumpSong(idx + 1, song)

def parseInputLine(l):
	args = []
	state = 0
	for c in l:
		if state == 0:
			if c in " \t": continue
			if c == "\n": break
			if c == "\"":
				args += [""]
				state = 1
				continue
			args += [c]
			state = 2
		elif state == 1: # in double quotation marks
			if c == "\"":
				state = 0
				continue
			args[-1] += c
		elif state == 2: # param
			if c in " \t":
				state = 0
				continue
			if c == "\n": break
			if c == "\"":
				args += [""]
				state = 1
				continue
			args[-1] += c
	return args

def handleConnection(conn, addr):
	print "mpdBackend: accepted", addr

	conn.setblocking(True)
	f = conn.makefile()
	session = Session(f)
	
	f.write("OK MPD %s\n" % MpdVersion)
	f.flush()
	
	import inspect
	while not f.closed:
		l = f.readline()
		if l == "": break
		input = parseInputLine(l)
		if input not in [["status"],["outputs"]]: # clients tend to spam these, so dont print these
			print "mpd conn:", input
		if not input:
			f.write("ACK [%i@0] {} No command given\n" % ACK_ERROR_UNKNOWN)
			f.flush()
			continue
		cmdName = input[0].lower()
		cmd = session.Commands.get(cmdName)
		if not cmd:
			f.write("ACK [%i@0] {} unknown command %r\n" % (ACK_ERROR_UNKNOWN, cmdName))
			f.flush()
			continue
		argspec = inspect.getargspec(cmd)
		if len(argspec.args) > len(input):
			f.write("ACK [%i@0] {%s} too few arguments for %r\n" % (ACK_ERROR_ARG, cmdName, cmdName))
			f.flush()
			continue	
		if len(argspec.args) < len(input) and argspec.varargs is None:
			f.write("ACK [%i@0] {%s} too many arguments for %r\n" % (ACK_ERROR_ARG, cmdName, cmdName))
			f.flush()
			continue	
		try:
			cmd(*input[1:])
			f.write("OK\n")
		except MpdException as e:
			f.write("ACK [%i@0] {%s} %s\n" % (e.errNum, cmdName, e.msg))			
		except Exception as e:
			f.write("ACK [%i@0] {%s} unknown exception %s : %s\n" % (ACK_ERROR_SYSTEM, cmdName, e.__class__.__name__, str(e)))
		finally:	
			f.flush()
		
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
