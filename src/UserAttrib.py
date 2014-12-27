
from utils import *
from Events import Event


class UserAttrib(object):
	""" The idea/plan for this attrib type is:
	Use it in the GUI and display it nicely. Store every GUI related info here.
	I.e. this should say whether it is read-only to the user (if not visible to user at all ->
	 don't use this class), if it should be represented as a list, string, etc.
	 (this is the type, right now all Traits.TraitTypes), some other GUI decoration stuff,
	 etc.
	Note that this lays in the utils module because it is completely decoupled
	from the GUI. It only stores information which might be useful for a GUI.
	"""

	staticCounter = 0

	class MetaAttribs:
		name = None
		type = None
		writeable = False
		updateHandler = None
		alignRight = False
		spaceX = None
		spaceY = None
		width = None
		height = None
		variableWidth = None
		variableHeight = False
		autosizeWidth = False
		highlight = False
		lowlight = False
		canHaveFocus = False
		withBorder = False
		searchLook = False
		autoScrolldown = False
		dragHandler = None
		selectionChangeHandler = None

	updateEventSlot = None

	def __init__(self, addUpdateEvent=False, **kwargs):
		# Keep an index. This is so that we know the order of initialization later on.
		# This is better for the GUI representation so we can order it the same way
		# as it is defined in the class.
		# iterUserAttribs() uses this.
		self.__class__.staticCounter += 1
		self.index = self.__class__.staticCounter

		for key in dir(self.MetaAttribs):
			if key.startswith("_"): continue
			setattr(self, key, getattr(self.MetaAttribs, key))
		for key, value in kwargs.iteritems():
			if key.startswith("_"):
				raise TypeError, "meta attrib %r invalid" % key
			if not hasattr(self.MetaAttribs, key):
				raise TypeError, "meta attrib %r unknown" % key
			setattr(self, key, value)
		self._addUpdateEvent = addUpdateEvent

	def getTypeClass(self):
		import inspect
		if inspect.isclass(self.type): return self.type
		return self.type.__class__
	def isType(self, T):
		return issubclass(self.getTypeClass(), T)
	@staticmethod
	def _getUserAttribDict(inst):
		if not hasattr(inst, "__userAttribs"):
			setattr(inst, "__userAttribs", {})
		return inst.__userAttribs
	@classmethod
	def _get(cls, name, inst):
		return cls._getUserAttribDict(inst)[name]
	def get(self, inst):
		try: return self._get(self.name, inst)
		except KeyError: return self.value
	def __get__(self, inst, type=None):
		if inst is None: # access through class
			return self
		if hasattr(self.value, "__get__"):
			return self.value.__get__(inst, type)
		return self.get(inst)
	@property
	def callDeco(self):
		class Wrapper:
			def __getattr__(_self, item):
				f = getattr(self.value, item)
				def wrappedFunc(arg): # a decorator expects a single arg
					value = f(arg)
					return self(value)
				return wrappedFunc
		return Wrapper()
	def hasUpdateEvent(self):
		return self.updateEventSlot
	def updateEvent(self, inst, type=None):
		return self.updateEventSlot.__get__(inst, type)
	@classmethod
	def _set(cls, name, inst, value):
		cls._getUserAttribDict(inst)[name] = value
	def set(self, inst, value):
		self._set(self.name, inst, value)
	def __set__(self, inst, value):
		if inst is None: # access through class
			self.value = value
			return
		if hasattr(self.value, "__set__"):
			self.value.__set__(inst, value)
		else:
			self.set(inst, value)
		if self.hasUpdateEvent():
			# Do it in a separate thread because we don't expect that some __set__
			# could perform badly or even result in some recursive call.
			import TaskSystem
			TaskSystem.daemonThreadCall(self.updateEvent, args=(inst,), name="%r update event callback" % self)
	@classmethod
	def _getName(cls, obj):
		if hasattr(obj, "name"): return obj.name
		elif hasattr(obj, "func_name"): return obj.func_name
		elif hasattr(obj, "fget"): return cls._getName(obj.fget)
		return None
	def __call__(self, attrib):
		if not self.name:
			self.name = self._getName(attrib)
		if self._addUpdateEvent:
			self.updateEventSlot = initBy(initFunc=lambda inst: Event(), name="%s_updateEvent" % self.name)
		self.value = attrib
		return self
	def __repr__(self):
		return "<UserAttrib %s, %r>" % (self.name, self.type)

def iterUserAttribs(obj):
	attribs = []
	for attribName in dir(obj.__class__):
		attrib = getattr(obj.__class__, attribName)
		if attrib.__class__.__name__ == "UserAttrib":
			attribs += [attrib]
	attribs.sort(key = lambda attr: attr.index)
	return attribs
