# experiment a bit with Traits

# http://docs.enthought.com/traits/traits_user_manual/index.html
# http://docs.enthought.com/traitsui/traitsui_user_manual/index.html
# http://code.enthought.com/projects/traits/examples.php


from traits.api import Delegate, HasTraits, TraitType

def delegateTrait(delegateObjName, baseType=None):
	class Trait(TraitType):
		def get(self, object, name):
			delegateObj = getattr(object, delegateObjName)
			return getattr(delegateObj, name)
	return Trait()

class State(HasTraits):
	mainState = None
	
	recentlyPlayedList = delegateTrait("mainState")
	curSong = delegateTrait("mainState")
	queue = delegateTrait("mainState")
	
	#traits_view = View()

from State import state as mainState
state = State()
state.mainState = mainState

import sys
try:
	# From TraitsUI. This prepares PyQt/PySide.
	import pyface.qt

	from PyQt4.QtCore import *
	from PyQt4.QtGui import *
	from PyQt4.QtWebKit import *
except:
	print "failed to import PyQt4"
	sys.excepthook(*sys.exc_info())
	print "This is mandatory. Install it with Homebrew by:"
	print "  brew install pyqt"
	print
	sys.exit(-1)

app = QApplication(sys.argv)

def guiMain():
	state.configure_traits()
