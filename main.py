#!/usr/bin/python
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# This is set to True when the startup was successful.
successStartup = False

import better_exchook
better_exchook.install()

try:
	import faulthandler
	faulthandler.enable(all_threads=True)
except ImportError:
	print "note: faulthandler module not available"
	faulthandler = None

# Do this early to do some option parsing and maybe special handling.
import appinfo

# Early check for "--profile".
# Enable profiling.
if __name__ == '__main__' and appinfo.args.profile:
	# No try/except. If requested and it fails -> exit.
	import cProfile
	profiler = cProfile.Profile()
	profiler.enable()
else:
	profiler = None

# Early check for forked process.
if __name__ == '__main__':
	import utils
	utils.ExecingProcess.checkExec()

# Early check for "--pyshell".
# This is a simple debug shell where we don't load anything.
if __name__ == '__main__' and appinfo.args.pyshell:
	better_exchook.simple_debug_shell({}, {})
	raise SystemExit

# Early check for "--pyexec".
# This is a simple Python execution where we don't load anything.
if __name__ == '__main__' and appinfo.args.pyexec:
	sourcecode = appinfo.args.pyexec[0]
	exec(compile(sourcecode, "<pyexec>", "exec"))
	raise SystemExit

def main():

	import utils
	import sys, time

	print "MusicPlayer", appinfo.version, "from", appinfo.buildTime, "git-ref", appinfo.gitRef[:10], "on", appinfo.platform, "(%s)" % sys.platform
	print "startup on", utils.formatDate(time.time())

	utils.setCurThreadName("Python main")

	try:
		# Hack: Make the `__main__` module also accessible as `main`.
		mainmod = sys.modules["__main__"]
		sys.modules.setdefault("main", mainmod)
		del mainmod
	except Exception:
		sys.excepthook(*sys.exc_info())
		# doesn't matter, continue

	# Import PyObjC here. This is because the first import of PyObjC *must* be
	# in the main thread. Otherwise, the NSAutoreleasePool created automatically
	# by PyObjC on the first import would be released at exit by the main thread
	# which would crash (because it was created in a different thread).
	# http://pyobjc.sourceforge.net/documentation/pyobjc-core/intro.html
	objc, AppKit = None, None
	try:
		import objc
	except Exception:
		if sys.platform == "darwin":
			print "Error while importing objc"
			sys.excepthook(*sys.exc_info())
		# Otherwise it doesn't matter.
	try:
		# Seems that the `objc` module is not enough. Without `AppKit`,
		# I still get a lot of
		#   __NSAutoreleaseNoPool(): ... autoreleased with no pool in place - just leaking
		# errors.
		if objc:
			import AppKit
	except Exception:
		# Print error in any case, also ImportError, because we would expect that this works.
		print "Error while importing AppKit"
		sys.excepthook(*sys.exc_info())


	from State import state, modules
	import stdinconsole
	import gui

	try:
		# This will overtake the main loop and raise SystemExit at its end.
		gui.main()
	except SystemExit:
		raise
	
	for m in modules: m.start()

	successStartup = True

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


if __name__ == '__main__':
	main()

