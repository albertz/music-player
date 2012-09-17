
class TraitType: pass

# These types just say what a property/UserAttrib/object should behave like, i.e. what protocol it should support.
# This is not really defined yet/strictly. It is used for now by the GUI.

class List(TraitType): pass
class OneLineText(TraitType): pass
class Enum(TraitType):
	def __init__(self, enums):
		self.enums = enums
class Object(TraitType): pass
class Action(TraitType): pass
class Image(TraitType): pass

# For now, it's just easier to have the song display (song thumbnail + play cursor)
# as a special type.
class SongDisplay(TraitType): pass
