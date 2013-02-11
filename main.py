#!/usr/bin/python
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import better_exchook
better_exchook.install()

try:
	import faulthandler
	faulthandler.enable(all_threads=True)
except ImportError:
	print "note: faulthandler module not available"

# Do this early to do some option parsing and maybe special handling.
import appinfo

# This might do some init which might be important to be done in the main thread.
import utils

utils.ExecingProcess.checkExec()

import sys, time
print "MusicPlayer", appinfo.version, "from", appinfo.buildTime, "on", appinfo.platform, "(%s)" % sys.platform
print "startup on", utils.formatDate(time.time())

from State import state, modules

if __name__ == '__main__':	

	import stdinconsole
	import gui

	try:
		# This will overtake the main loop and raise SystemExit at its end.
		gui.main()
	except SystemExit:
		raise
	
	for m in modules: m.start()

	# Note on quit behavior: Simply iterating state.updates
	# and waiting for its end does not work because we would
	# not interrupt on signals, e.g. KeyboardInterrupt.
	# It is also not possible (in general) to catch
	# signals from other threads, thus we have to do it here.
	# time.sleep() is a good way to wait for signals.
	# However, we use stdinconsole.readNextInput() because
	# there is simply no way to have os.read() in another thread
	# and to be able to interrupt that from here (the main thread).
	# In other threads: thread.interrupt_main() does not work
	# for time.sleep() (or at least it will not interrupt the sleep).
	# os.kill(0, signal.SIGINT) works, though.
	# To interrupt/stop all threads:
	# signal.set_wakeup_fd(sys.stdin.fileno()) also does not really
	# work to interrupt the stdin thread, probably because stdin is
	# not non-blocking.
	# Every thread must only wait on a OnRequestQueue which registers
	# itself in its thread. We cancelAll() here already the main queue
	# (state.updates) and in Module.stop(), we also cancel any custom
	# queue.

	while True:
		try: stdinconsole.readNextInput() # wait for KeyboardInterrupt
		except BaseException, e:
			state.updates.put((e, (), {}))
			state.updates.cancelAll()
			break
	for m in modules: m.stop()


