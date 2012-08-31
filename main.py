#!/usr/bin/python

import better_exchook
better_exchook.install()

from utils import *
from State import state

modules = map(Module, [
	"player",
	"tracker",
	"mediakeys",
	"gui",
	"stdinconsole",
])

if __name__ == '__main__':	
	import time, os, sys

	for m in modules: m.start()
	# Note on quit behavior: Simply iterating state.updates
	# and waiting for its end does not work because we would
	# not interrupt on signals, e.g. KeyboardInterrupt.
	# It is also not possible (in general) to catch
	# signals from other threads, thus we have to do it here.
	# time.sleep() is a good way to wait for signals.
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
		try: time.sleep(10) # wait for KeyboardInterrupt
		except BaseException, e:
			state.updates.put((e, (), {}))
			state.updates.cancelAll()
			break
	os.close(sys.stdin.fileno())
	for m in modules: m.stop()
	
	