# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# This is an implementation of the [MPD protocol](http://www.musicpd.org/doc/protocol/).

Debug = False
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

class Session(object):
	def __init__(self, f):
		self.f = f
		self.playlist = None
		self.playlistIdx = 0
		self.baseIdx = 0
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
	
	@property
	def _volumeMax(self):
		assert state.__class__.volume.type.min == 0
		return float(state.__class__.volume.type.max)

	@property
	def _volume(self):
		return float(state.volume)

	@property
	def volume(self):
		return int((self._volume / self._volumeMax) * 100.0)

	@volume.setter
	def volume(self, v):
		state.volume = (float(v) / 100.0) * self._volumeMax

	def cmdSetVol(self, vol):
		vol = int(vol)
		self.volume = vol

	def cmdStatus(self):
		# see mpd_getStatus in https://github.com/TheStalwart/Theremin/blob/master/libmpdclient-0.18.96/src/libmpdclient.c
		f = self.f
		if state.player.playing:
			f.write("state: play\n")
		else:
			f.write("state: pause\n")
		if self.playlist is not None:
			while self.baseIdx < len(self.playlist):
				if self.playlist[self.baseIdx] == state.curSong:
					break
				self.baseIdx += 1
			if self.baseIdx >= len(self.playlist):
				self.baseIdx = 0
				self.playlist = None
				self.playlistIdx += 1 # we need a reload
			else:
				curQueueList = list(state.queue.queue.list)
				if self.playlist[self.baseIdx+1:] != curQueueList:
					# the list was changed -> we need a reload
					self.baseIdx = 0
					self.playlist = None
					self.playlistIdx += 1 # we need a reload					
		f.write("playlist: %i\n" % self.playlistIdx)
		if self.playlist is None:
			f.write("playlistlength: %i\n" % (len(state.queue.queue.list) + 1))
		else:
			f.write("playlistlength: %i\n" % len(self.playlist))
		f.write("volume: %i\n" % self.volume)
		f.write("song: %i\n" % self.baseIdx)
		f.write("songid: %i\n" % self.baseIdx)
		f.write("nextsong: %i\n" % (self.baseIdx + 1))
		f.write("nextsongid: %i\n" % (self.baseIdx + 1))
		f.write("time: %i:%i\n" % (state.player.curSongPos, state.player.curSongLen))
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
		# we ignore playid by purpose. we don't want the 'skip-to-random-song' behavior
		# in this music-player.
		state.player.playing = True
	
	def cmdPause(f, pause=True):
		state.player.playing = not pause
	
	def cmdStop(f, *args):
		state.player.playing = False
	
	def cmdNext(f):
		state.player.nextSong()
	
	def cmdPrevious(f):
		# not even supported in the main state controller (yet)
		pass
	
	def dumpSong(self, songid, song):
		f = self.f
		f.write("file: %s\n" % getattr(song, "url", "").encode("utf8"))
		f.write("Artist: %s\n" % getattr(song, "artist", "<unknown>").encode("utf8"))
		f.write("Title: %s\n" % getattr(song, "title", "<unknown>").encode("utf8"))
		f.write("Album: %s\n" % getattr(song, "album", "").encode("utf8"))
		f.write("Genre: %s\n" % ", ".join([key for (key,value) in sorted(getattr(song, "tags", {}).items()) if value > 0.8]).encode("utf8"))
		f.write("Time: %i\n" % getattr(song, "duration", 0))
		f.write("Pos: %i\n" % songid)
		f.write("Id: %i\n" % songid)
	
	def cmdCurrentSong(self):
		self.dumpSong(self.baseIdx, state.curSong)
		
	def cmdPlaylistId(self, listid):
		listid = int(listid)
		if self.playlist is None:
			self._initPlaylist()
		try:
			song = self.playlist[listid]
		except IndexError:
			raise MpdException(errNum=ACK_ERROR_NO_EXIST, msg="No such song (id %i, listlen %i)" % (listid, len(self.playlist)))
		self.dumpSong(listid, song)
	
	def _initPlaylist(self):
		self.playlist = []
		self.playlist += [state.curSong.__get__(None)]
		self.playlist += list(state.queue.queue.list)
		self.baseIdx = 0
		
	def cmdPlChanges(self, version):
		self._initPlaylist()
		for idx,song in enumerate(self.playlist):
			self.dumpSong(idx, song)

	def cmdSeek(self, songPos, songTime):
		songPos = int(songPos)
		if songPos != self.baseIdx: return # only seeking of current song supported
		self.cmdSeekCur(songTime)
		
	def cmdSeekId(self, songId, songTime):
		songId = int(songId)
		if songId != self.baseIdx: return # only seeking of current song supported
		self.cmdSeekCur(songTime)
	
	def cmdSeekCur(self, songTime):
		songTime = int(songTime)
		state.player.seekAbs(songTime)
	
	def cmdIdle(self, subsystems=None):
		# this is not really supported. just dummy output:
		time.sleep(0.1)
		for subsystem in ["playlist", "player"]:
			self.f.write("changed: %s\n" % subsystem)
	
	def cmdClearError(self):
		# there aren't any errors (yet)
		pass
	
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
	
	import inspect, socket
	while not f.closed:
		try:
			l = f.readline()
			if l == "": break
			input = parseInputLine(l)
			if Debug:
				if input not in [["status"],["outputs"],["idle"],["noidle"]]: # clients tend to spam these, so dont print these
					print "mpd conn:", input
			cmdListIdx = 0
			if not input:
				f.write("ACK [%i@%i] {} No command given\n" % (ACK_ERROR_UNKNOWN, cmdListIdx))
				f.flush()
				continue
			cmdName = input[0].lower()
			if cmdName == "noidle": continue # special handling. there must be no "OK" here
			cmd = session.Commands.get(cmdName)
			if not cmd:
				f.write("ACK [%i@%i] {} unknown command %r\n" % (ACK_ERROR_UNKNOWN, cmdListIdx, cmdName))
				f.flush()
				continue
			argspec = inspect.getargspec(cmd)
			minArgCount = len(argspec.args) - 1 - len(argspec.defaults or [])
			maxArgCount = float("inf") if argspec.varargs else len(argspec.args) - 1
			if len(input) - 1 < minArgCount:
				f.write("ACK [%i@%i] {%s} too few arguments for %r (min: %s)\n" % (ACK_ERROR_ARG, cmdListIdx, cmdName, cmdName, minArgCount))
				f.flush()
				continue	
			if len(input) - 1 > maxArgCount:
				f.write("ACK [%i@%i] {%s} too many arguments for %r (max: %s)\n" % (ACK_ERROR_ARG, cmdListIdx, cmdName, cmdName, maxArgCount))
				f.flush()
				continue	
			try:
				cmd(*input[1:])
				f.write("OK\n")
			except MpdException as e:
				f.write("ACK [%i@%i] {%s} %s\n" % (e.errNum, cmdListIdx, cmdName, e.msg))			
			except Exception as e:
				f.write("ACK [%i@%i] {%s} unknown exception %s : %s\n" % (ACK_ERROR_SYSTEM, cmdListIdx, cmdName, e.__class__.__name__, str(e)))
			finally:	
				f.flush()
		except socket.error as e:
			print e
			break

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
	if not appinfo.config.mpdBackend: return
	host = appinfo.config.mpdBindHost
	port = appinfo.config.mpdBindPort
	
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
