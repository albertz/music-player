# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.


import appinfo
import sys
from utils import safe_property, do_in_mainthread


# define fallback
def main(): raise NotImplementedError
def guiMain(): pass
def locateFile(filename):
	print "locateFile", utils.convertToUnicode(filename).encode("utf-8")

def about():
	import webbrowser
	webbrowser.open("http://albertz.github.io/music-player/")


if not appinfo.args.nogui:
	from _gui import *

	try:
		# Right now, we can only enable qtgui via cmdline and the only
		# two implementations are Cocoa and Qt. And we always try to enable
		# one of these implementations. That is why the selection looks like
		# this.
		# Later, it might sense to disable the GUI at all and there might be
		# other GUI implementations. Also, maybe the design might change and
		# we could enable multiple GUIs as different separate modules.
		# E.g., the webinterface will in any case be a separate module.
		if sys.platform == "darwin" and not appinfo.args.qtgui:
			from guiCocoa import *
		else:
			# Use Qt as the generic fallback.
			from guiQt import *
	except Exception:
		print "error in loading GUI implementation"
		sys.excepthook(*sys.exc_info())


class _GuiObject:

	def __repr__(self): return "<%s %r %r>" % (self.__class__.__name__, self.subjectObject, self.attr)

	@safe_property
	@property
	def name(self):
		name = ""
		obj = self
		while True:
			if obj.parent:
				name = "." + obj.attr.name + name
				obj = obj.parent
			else:
				name = obj.subjectObject.__class__.__name__ + name
				break
		return name

	def allParents(self):
		obj = self
		while obj:
			yield obj
			obj = obj.parent

	def childIter(self): return self.childs.itervalues()
	
	def updateSubjectObject(self):
		if self.parent:
			self.subjectObject = self.attr.__get__(self.parent.subjectObject)
		if getattr(self.subjectObject, "_updateEvent", None):
			self._updateHandler = lambda: do_in_mainthread(self.updateContent, wait=False)
			getattr(self.subjectObject, "_updateEvent").register(self._updateHandler)

	def updateChild(self, child):
		if child.attr and child.attr.updateHandler:
			try:
				child.attr.updateHandler(self.subjectObject, child.attr)
			except Exception:
				sys.excepthook(*sys.exc_info())
		child.updateContent()

	def updateContent(self):
		self.updateSubjectObject()
		for control in self.childIter():
			self.updateChild(control)

	def guiObjectsInLine(self):
		obj = self
		while True:
			if not getattr(obj, "leftGuiObject", None): break
			obj = obj.leftGuiObject
		while obj:
			yield obj
			obj = getattr(obj, "rightGuiObject", None)

	def layoutLine(self):
		"""
		In the parent, it searches for all objects which are in (horizontal) line
		with us (via `guiObjectsInLine`). It then layouts their x-pos and sets
		the autoresize mask on those controls.
		"""
		line = list(self.guiObjectsInLine())
		minY = min([control.pos[1] for control in line])
		maxH = max([control.size[1] for control in line])

		# Set x-pos from left to right.
		# XXX: Haven't we done this already in setupChilds()?
		x = self.parent.OuterSpace[0]
		for control in line:
			spaceX = self.parent.DefaultSpace[0]
			if control.attr.spaceX is not None: spaceX = control.attr.spaceX

			w,h = control.size
			y = minY + (maxH - h) / 2.
			
			control.pos = (x,y)
			
			x += w + spaceX

		# Search the variable-width-control.
		varWidthControl = None
		for control in line:
			if control.attr.variableWidth:
				varWidthControl = control
				break
		if not varWidthControl:
			varWidthControl = line[-1]
			if varWidthControl.attr.variableWidth is False:
				# It explicitly doesn't want to be of variable size.
				# We can return because there is nothing to do anymore.
				return

		x = self.parent.innerSize[0] - self.parent.OuterSpace[0]
		for control in reversed(line):
			w,h = control.size
			y = control.pos[1]
	
			if control is varWidthControl:
				w = x - control.pos[0]
				x = control.pos[0]
				control.pos = (x,y)
				control.size = (w,h)
				control.autoresize = control.autoresize[:2] + (True,) + control.autoresize[3:]
				control.layout()
				break
			else:
				x -= w
				control.pos = (x,y)
				control.size = (w,h)
				control.autoresize = (True,) + control.autoresize[1:]

				spaceX = self.parent.DefaultSpace[0]
				if control.attr.spaceX is not None: spaceX = control.attr.spaceX
				x -= spaceX
	
	def childGuiObjectsInColumn(self):
		obj = self.firstChildGuiObject
		while obj:
			yield obj
			while getattr(obj, "rightGuiObject", None):
				obj = obj.rightGuiObject
			obj = getattr(obj, "bottomGuiObject", None)
		
	def layout(self):
		"""
		This layouts all the child controls according to our size,
		and sets its autoresize mask.
		In this function itself, we handle the variable-height-control,
		and we call `layoutLine()` to handle the variable-width-controls.
		"""

		lastVertControls = list(self.childGuiObjectsInColumn())
		if not lastVertControls: return

		# Search variable-height-control.
		varHeightControl = None
		for control in lastVertControls:
			if control.attr.variableHeight:
				varHeightControl = control
				break
		if not varHeightControl:
			varHeightControl = lastVertControls[-1]
			if varHeightControl.attr.variableHeight is False:
				# It explicitly doesn't want to be of variable size.
				varHeightControl = None

		# Set y-pos from top to bottom, until we get to the varHeightControl.
		# XXX: Exactly this is already done in setupChilds, isn't it?
		if False:
			y = self.OuterSpace[1]
			for control in lastVertControls:
				if control is varHeightControl: break

				x = control.pos[0]
				control.pos = (x,y)

				if control.attr.spaceY is not None: y += control.attr.spaceY
				else: y += self.DefaultSpace[1]
				y += control.size[1]

		if varHeightControl:
			# Set y-pos from bottom to top, until we get to the varHeightControl.
			y = self.innerSize[1] - self.OuterSpace[1]
			for control in reversed(lastVertControls):
				w,h = control.size
				x = control.pos[0]

				if control is varHeightControl:
					h = y - control.pos[1]
					y = control.pos[1]
					control.pos = (x,y)
					control.size = (w,h)
					control.autoresize = control.autoresize[0:3] + (True,)
					# The size has changed, thus update its layout.
					control.layout()
					break
				else:
					y -= h
					for lineControl in control.guiObjectsInLine():
						lineControl.pos = (lineControl.pos[0],y)
						lineControl.autoresize = lineControl.autoresize[0:1] + (True,) + lineControl.autoresize[2:4]
					y -= self.DefaultSpace[1]

		for control in lastVertControls:
			control.layoutLine()

		# If we are not auto-resizable in height,
		# set our own height according to the last control.
		if not self.autoresize[3]:
			w,h = self.size
			lastCtr = lastVertControls[-1]
			h = lastCtr.pos[1] + lastCtr.size[1]
			self.size = (w,h)

	firstChildGuiObject = None
	childs = {} # (attrName -> guiObject) map. this might change...
	def setupChilds(self):
		"""
		If this is a container (a generic object), this creates + setups the child controls.
		It does some initial layouting, also to calculate a size-indication, which is then returned.
		However, you can set another size after it and you are supposed to call `layout()`
		in the end.
		"""

		#self.updateSubjectObject() # XXX: make it explicit? break simple list interface
		self.firstChildGuiObject = None
		self.childs = {}
		x, y = self.OuterSpace
		maxX, maxY = 0, 0
		lastControl = None

		from utils import iterUserAttribs
		for attr in iterUserAttribs(self.subjectObject):
			try:
				control = buildControl(attr, self)
			except NotImplementedError as e:
				print e
				# Skip this control and continue. The rest of the GUI might still be usable.
				continue
			if not self.firstChildGuiObject:
				self.firstChildGuiObject = control
			if attr.hasUpdateEvent():
				def controlUpdateHandler(control=control):
					do_in_mainthread(lambda: self.updateChild(control), wait=False)
				control._updateHandler = controlUpdateHandler
				attr.updateEvent(self.subjectObject).register(control._updateHandler)
			self.addChild(control)
			self.childs[attr.name] = control

			spaceX, spaceY = self.DefaultSpace
			if attr.spaceX is not None: spaceX = attr.spaceX
			if attr.spaceY is not None: spaceY = attr.spaceY
			
			if attr.alignRight and lastControl: # align next right
				x = lastControl.pos[0] + lastControl.size[0] + spaceX
				# y from before
				control.leftGuiObject = lastControl
				if lastControl:
					lastControl.rightGuiObject = control
				
			elif lastControl: # align next below
				x = self.OuterSpace[0]
				y = maxY + spaceY
				control.topGuiObject = lastControl
				if lastControl:
					lastControl.bottomGuiObject = control

			else: # very first
				pass

			control.pos = (x,y)
			control.autoresize = (False,False,False,False) # initial, might get changed in `layout()`

			lastControl = control
			maxX = max(maxX, control.pos[0] + control.size[0])
			maxY = max(maxY, control.pos[1] + control.size[1])
		
			control.updateContent()

		# Recalculate layout based on current size and variable width/height controls.
		# Note that there are some cases where this recalculation is not needed,
		# but its much easier to just call it always now.
		self.layout()

		# Handy for now. This return might change.
		return (maxX + self.OuterSpace[0], maxY + self.OuterSpace[1])



def handleApplicationQuit():
	"""
	Depending on the environment, this might be called multiple times.
	It should do some cleanup and save the DBs and such.

	Once this get called, the app is not expected to be in a
	functional state anymore.
	"""

	import utils
	if utils.quit > 1: return # Already called before.
	utils.quit = 1

	# first set/send signals to all modules
	from State import modules
	for m in modules: m.stop(join=False)
	try:
		# in case there are any subprocesses, interrupt them
		# maybe some modules are hanging and waiting for such
		import sys, os, signal
		os.kill(0, signal.SIGINT)
	except KeyboardInterrupt: pass # well, we expect that...
	except Exception: pass

	# now join all
	for m in modules: m.stop()

	# Do some cleanup before we let Python do the final cleanup.
	# E.g., it might happen that Python will not GC the player instance
	# soon enough in its `Py_Finalize()`. In that situation, bad things
	# will happen, because most probably, the player instances worker
	# thread is still running in the background. This most probably
	# leads to a crash.
	RootObjs.clear()
	try: ctx().rootObjs.clear()
	except Exception: pass # might already be out of scope
	import State
	State.state = None
	import songdb
	songdb.flush()
	import gc
	for _ in range(3): gc.collect()

	utils.quit = 2
	print "Bye!"


# On Mac/Win/Linux, these are the windows.
RootObjs = {}

class RootObj(object):
	obj = None
	guiObj = None
	name = "Object"
	title = None
	priority = -10
	keyShortcut = None

	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			if not hasattr(self, key): raise AttributeError, "%s invalid" % key
			if key.startswith("_"): raise AttributeError, "%s is read-only" % key
			setattr(self, key, value)
		if self.title is None: self.title = self.name
		if self.__class__ is RootObj and self.obj is None:
			raise AttributeError, "obj must be set"

def registerRootObj(**kwargs):
	desc = RootObj(**kwargs)
	RootObjs[desc.name] = desc

class CtxRootObj(RootObj):
	clazz = None

	@property
	def _rootObj(self):
		c = ctx()
		if self.name in c.rootObjs:
			return c.rootObjs[self.name]
		obj = self.clazz(ctx=c)
		attribs = dict([(key,getattr(self,key)) for key in dir(self) if not key.startswith("_")])
		del attribs["obj"]
		rootObj = RootObj(obj=obj, **attribs)
		c.rootObjs[self.name] = rootObj
		return rootObj

	@property
	def obj(self): return self._rootObj.obj

	@property
	def guiObj(self): return self._rootObj.guiObj
	@guiObj.setter
	def guiObj(self, value): self._rootObj.guiObj = value

def registerCtxRootObj(**kwargs):
	desc = CtxRootObj(**kwargs)
	RootObjs[desc.name] = desc

def iterRootObjs():
	objs = list(RootObjs.values())
	objs.sort(key=lambda o: o.priority, reverse=True)
	return objs


# This function is later supposed to give the right gui context
# depending where we call it from. This can maybe be managed/set via
# contextlib or so.
# The context itself is supposed to provide objects like window list,
# current selected song (needed for SongEdit), etc.
# Right now, we just support a single context.
def ctx():
	global _ctx
	if _ctx: return _ctx
	from utils import Event, initBy
	class Ctx(object):
		# context-based root objects. via registerCtxRootObj()
		@initBy
		def rootObjs(self): return {}

		@property
		def curSelectedSong(self):
			song = getattr(self, "_curSelectedSong", None)
			if song: return song
			# otherwise fall back to current song.
			# it's better to have always one so if the window is created,
			# the layout is correct.
			# this is actually a hack: better would be if the re-layouting
			# would work correctly in that case. we really should work
			# out some generic nice and clean update-handling...
			import State
			return State.state.curSong
		
		@curSelectedSong.setter
		def curSelectedSong(self, obj):
			self._curSelectedSong = obj
			self.curSelectedSong_updateEvent.push()
			
		@initBy
		def curSelectedSong_updateEvent(self): return Event()

	_ctx = Ctx()
	return _ctx
_ctx = None
