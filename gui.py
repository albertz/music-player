# experiment a bit with Traits

# http://docs.enthought.com/traits/traits_user_manual/index.html
# http://docs.enthought.com/traitsui/traitsui_user_manual/index.html
# http://code.enthought.com/projects/traits/examples.php


from traits.api import Delegate, HasTraits, Instance, Int, Str

class State(HasTraits):
	mainState = None
	
	recentlyPlayedList = Delegate("mainState")
	curSong = Delegate("mainState")
	queue = Delegate("mainState")
	
	#traits_view = View()

from State import state as mainState
state = State()
state.mainState = mainState

def guiMain():	
	state.configure_traits()
