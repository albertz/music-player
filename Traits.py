
from contextlib import contextmanager

class TraitType: pass

# These types just say what a property/UserAttrib/object should behave like, i.e. what protocol it should support.
# This is not really defined yet/strictly. It is used for now by the GUI.

class List(TraitType):
	def onInsert(self, index, value): pass
	def onRemove(self, index): pass
	def onClear(self): pass
	
	@property
	@contextmanager
	def lock(self): yield
	
	def insert(self, index, value): pass
	def remove(self, index): pass
	def clear(self): pass
	def __getitem__(self, index): pass
	def __len__(self): pass
	
class Table(TraitType):
	def onInsert(self, index, value): pass
	def onRemove(self, index): pass
	def onClear(self): pass
	
	@property
	@contextmanager
	def lock(self): yield
	
	def insert(self, index, value): pass
	def remove(self, index): pass
	def clear(self): pass
	def __getitem__(self, index): pass
	def __len__(self): pass
	

class EditableText(TraitType): pass
class OneLineText(TraitType): pass
class ClickableLabel(TraitType): pass
class Enum(TraitType):
	def __init__(self, enums):
		self.enums = enums
class Object(TraitType): pass
class Action(TraitType): pass
class Image(TraitType): pass

# For now, it's just easier to have the song display (song thumbnail + play cursor)
# as a special type.
class SongDisplay(TraitType): pass
