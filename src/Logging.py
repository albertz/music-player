
"""
We provide a system to log any information messages, warnings or errors.
Most of them are meant to be read for developers, also they might also
be helpful for users in case something doesn't work.
"""

import better_exchook


def debugWarn(msg):
	print "Warning:", msg
	import sys
	if not hasattr(sys, "_getframe"):
		print "Warning: debugWarn: no sys._getframe"
		return
	f = sys._getframe()
	if not f:
		print "Warning: debugWarn: no frame"
	f = f.f_back
	if not f:
		print "Warning: debugWarn: no previous frame"
	better_exchook.print_traceback(f)
