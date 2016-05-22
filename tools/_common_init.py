
import sys, os

importPath = os.path.join(os.path.dirname(__file__), "../src")
assert os.path.exists("%s/better_exchook.py" % importPath), "MusicPlayer source path seems invalid: %r" % importPath

if importPath not in sys.path:
	sys.path += [importPath]

import better_exchook
better_exchook.install()
