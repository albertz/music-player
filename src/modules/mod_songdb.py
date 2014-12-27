

def songdbMain():
	# Import modules, which will have the side-effect to
	# init/load the songdb (lazily) and register the GUI.
	import songdb
	import Search

	# This is heavy, ugly, etc...
	# But it's simple nice hack for now to index everything.
	import TaskSystem
	def indexAll():
		import appinfo
		for dir in appinfo.musicdirs:
			TaskSystem.asyncCall(lambda: songdb.indexSearchDir(dir), name="create search index", mustExec=True)
	TaskSystem.daemonThreadCall(indexAll, name="create search index")

	# Reindex played songs.
	from State import state
	from Player import PlayerEventCallbacks
	for ev,args,kwargs in state.updates.read():
		try:
			if ev is PlayerEventCallbacks.onSongChange:
				newSong = kwargs["newSong"]
				songdb.insertSearchEntry(newSong)
		except Exception:
			import sys
			sys.excepthook(*sys.exc_info())
	songdb.flush()
