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
	
	def _resetPlaylist(self):
		self.baseIdx = 0
		self.playlist = None
		self.playlistIdx += 1 # force a reload

	def _checkPlaylist(self):
		if self.playlist is not None:
			while self.baseIdx < len(self.playlist):
				if self.playlist[self.baseIdx] == state.curSong:
					break
				self.baseIdx += 1
			if self.baseIdx >= len(self.playlist):
				self._resetPlaylist() # we need a reload
				return False
			else:
				curQueueList = list(state.queue.queue.list)
				if self.playlist[self.baseIdx+1:] != curQueueList:
					# the list was changed -> we need a reload
					self._resetPlaylist()
					return False
			return True
		return False
	
	def cmdStatus(self):
		# see mpd_getStatus in https://github.com/TheStalwart/Theremin/blob/master/libmpdclient-0.18.96/src/libmpdclient.c
		f = self.f
		if state.player.playing:
			f.write("state: play\n")
		else:
			f.write("state: pause\n")
		self._checkPlaylist()
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
	
	def cmdListAllInfo(self, dir=None):
		# this is a hack for some clients.
		# some clients seem to need some data here.
		# just list the songs from the queue.		
		for song in list(state.queue.queue.list):
			self.dumpSong(song=song)
	
	def cmdLsInfo(self, dir):
		import os, appinfo
		from Song import Song
		basedir = appinfo.musicdirs[0]
		for fn in os.listdir(basedir + "/" + dir):
			fullfn = basedir + "/" + dir + "/" + fn
			if os.path.isdir(fullfn):
				self.f.write("directory: %s\n" % ((dir + "/" + fn).strip("/")))
			elif os.path.isfile(fullfn):
				ext = os.path.splitext(fn)[1].lower()
				if ext[:1] == ".": ext = ext[1:]
				if ext in appinfo.formats:
					song = Song(url=fullfn)
					if song:
						self.dumpSong(song=song)

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
	
	def dumpSong(self, song, songid=None):
		f = self.f
		url = getattr(song, "url", "").encode("utf8")
		import appinfo
		basedir = appinfo.musicdirs[0] + "/"
		if url.startswith(basedir):
			url = url[len(basedir):]
		assert url
		f.write("file: %s\n" % url)
		#f.write("Last-Modified: 2013-02-12T01:44:17Z\n") # dummy
		d = []
		d += [("Time", str(int(getattr(song, "duration", 0))))]
		d += [("Artist", getattr(song, "artist", "<unknown>").encode("utf8"))]
		d += [("Title", getattr(song, "title", "<unknown>").encode("utf8"))]
		d += [("Album", getattr(song, "album", "").encode("utf8"))]
		d += [("Genre", ", ".join([key for (key,value) in sorted(getattr(song, "tags", {}).items()) if value > 0.8]).encode("utf8"))]
		for (key,value) in d:
			if not value: continue
			f.write("%s: %s\n" % (key,value))		
		if songid is not None:
			f.write("Pos: %i\n" % songid)
			f.write("Id: %i\n" % songid)
	
	def cmdCurrentSong(self):
		self.dumpSong(song=state.curSong, songid=self.baseIdx)
		
	def cmdPlaylistId(self, listid):
		listid = int(listid)
		if self.playlist is None:
			self._initPlaylist()
		try:
			song = self.playlist[listid]
		except IndexError:
			raise MpdException(errNum=ACK_ERROR_NO_EXIST, msg="No such song (id %i, listlen %i)" % (listid, len(self.playlist)))
		self.dumpSong(songid=listid, song=song)
	
	def _initPlaylist(self):
		self.playlist = []
		self.playlist += [state.curSong.__get__(None)]
		self.playlist += list(state.queue.queue.list)
		self.baseIdx = 0
		
	def cmdPlChanges(self, version):
		self._initPlaylist()
		for idx,song in enumerate(self.playlist):
			self.dumpSong(songid=idx, song=song)

	def cmdPlaylistInfo(self, songpos=None):
		if self.playlist is None:
			self._initPlaylist()
		for idx,song in enumerate(self.playlist):
			self.dumpSong(songid=idx, song=song)		

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
	
	_oldBaseIdx = 0
	_oldPlayState = None
	def cmdIdle(self, subsystems=None):
		# this is not really supported. just dummy output:
		time.sleep(0.1)
		changedSubsystems = set()
		if self._oldBaseIdx != self.baseIdx:
			changedSubsystems.add("player")
		self._oldBaseIdx = self.baseIdx
		if self._oldPlayState != state.player.playing:
			changedSubsystems.add("player")
		self._oldPlayState = state.player.playing
		if not self._checkPlaylist():
			changedSubsystems.add("playlist")
		for subsystem in changedSubsystems:
			self.f.write("changed: %s\n" % subsystem)
	
	def cmdClearError(self):
		# there aren't any errors (yet)
		pass
	
	def cmdDecoders(self):
		import appinfo
		for suffix in appinfo.formats:
			self.f.write("suffix: %s\n" % suffix)
	
	def cmdAddId(self, url, position=None):
		if url.startswith("file://"):
			url = url[len("file://"):]
		if url[:1] != "/":
			import appinfo
			basedir = appinfo.musicdirs[0] + "/"
			url = basedir + url
		import os
		assert os.path.exists(url), "%s not found" % url
		from Song import Song
		song = Song(url=url)
		assert song, "cannot load song"
		with state.queue.queue.lock:
			if position is None:
				position = len(state.queue.queue)
			else:
				position = int(position)
				position -= self.baseIdx + 1
				if position > len(state.queue.queue):
					position = len(state.queue.queue)
				elif position < 0:
					position = 0
			state.queue.queue.insert(position, song)
		self.f.write("Id: %i\n" % (self.baseIdx + position + 1))
		# songids are messed up now. force reload
		self._resetPlaylist()

	def cmdDeleteId(self, songid):
		with state.queue.queue.lock:
			self._checkPlaylist()
			if self.playlist is None: return # songid might be wrong
			songid = int(songid)
			songid -= self.baseIdx + 1
			if songid < 0: return
			if songid > len(state.queue.queue): return
			state.queue.queue.remove(songid)
		# songids are messed up now. force reload
		self._resetPlaylist()
	
	def cmdClear(self):
		# we don't allow that to avoid some accidental missue
		# however, the client probably should update its playlist
		self._resetPlaylist()
		
	def cmdSearch(self, type, what):
		# ignore type. assume "any". anything else anyway not supported yet
		what = what.strip()
		if not what: return
		import songdb
		res = songdb.search(what)
		from Song import Song
		import os
		for entry in res:
			url = entry["url"]
			if not os.path.exists(url): continue
			song = Song(url=url)
			self.dumpSong(song=song)
	
	def cmdListPlaylists(self):
		# not supported yet
		pass

	def cmdSticker(self, *args):
		# not supported yet
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
			if input == ["noidle"]: continue # special handling. there must be no "OK" here
			cmdListIdx = 0
			listinput = []
			listtype = 0
			if input == ["command_list_begin"]:
				listtype = 1
			elif input == ["command_list_ok_begin"]:
				listtype = 2
			else:
				listinput = [input]
			if listtype:
				while True:
					l = f.readline()
					assert l != ""
					input = parseInputLine(l)
					if input == ["command_list_end"]: break
					listinput += [input]
			isOk = True
			for cmdListIdx,input in enumerate(listinput):
				if Debug:
					if input not in [["status"],["outputs"],["idle"]]: # clients tend to spam these, so dont print these
						print "mpd conn:", input
				isOk = False
				if not input:
					f.write("ACK [%i@%i] {} No command given\n" % (ACK_ERROR_UNKNOWN, cmdListIdx))
					break
				cmdName = input[0].lower()
				if cmdName == "noidle": continue 
				cmd = session.Commands.get(cmdName)
				if not cmd:
					f.write("ACK [%i@%i] {} unknown command %r\n" % (ACK_ERROR_UNKNOWN, cmdListIdx, cmdName))
					break
				argspec = inspect.getargspec(cmd)
				minArgCount = len(argspec.args) - 1 - len(argspec.defaults or [])
				maxArgCount = float("inf") if argspec.varargs else len(argspec.args) - 1
				if len(input) - 1 < minArgCount:
					f.write("ACK [%i@%i] {%s} too few arguments for %r (min: %s)\n" % (ACK_ERROR_ARG, cmdListIdx, cmdName, cmdName, minArgCount))
					break	
				if len(input) - 1 > maxArgCount:
					f.write("ACK [%i@%i] {%s} too many arguments for %r (max: %s)\n" % (ACK_ERROR_ARG, cmdListIdx, cmdName, cmdName, maxArgCount))
					break	
				try:
					cmd(*input[1:])
					isOk = True
					if listtype == 2:
						f.write("list_OK\n")
						f.flush()
				except MpdException as e:
					f.write("ACK [%i@%i] {%s} %s\n" % (e.errNum, cmdListIdx, cmdName, e.msg))
					break
				except Exception as e:
					if Debug:
						print "mdpBackend: exception: %s : %s" % (e.__class__.__name__, str(e))
					f.write("ACK [%i@%i] {%s} unknown exception %s : %s\n" % (ACK_ERROR_SYSTEM, cmdListIdx, cmdName, e.__class__.__name__, str(e)))
					break
			if isOk:
				f.write("OK\n")
			f.flush()
		except socket.error as e:
			print "mpdBackend: socket.error: %s" % e
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
