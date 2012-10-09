
import sys

from guiCocoa import *

class GuiObject:
	"This defines the protocol we must support"
	
	parent = None
	attr = None # if this is a child of something, this is the access attrib of the parent.subjectObject
	pos = (0,0)
	size = (0,0)
	autoresize = (False,False,False,False) # wether to modify x,y,w,h on resize
	nativeGuiObject = None	
	subjectObject = None
	DefaultSpace = (8,8)
	OuterSpace = (8,8)
	
	@property
	def innerSize(self): return self.size
	
	def layoutSize(self): pass	
	def addChild(self, childGuiObject): pass

	def updateContent(self, ev, args, kwargs):
		for control in self.childs.values():
			if control.attr.updateHandler:
				try:
					control.attr.updateHandler(self.subjectObject, control.attr, ev, args, kwargs)
				except:
					sys.excepthook(*sys.exc_info())
			control.updateContent(ev, args, kwargs)
	
	def guiObjectsInLine(self):
		obj = self
		while True:
			if not getattr(obj, "leftGuiObject", None): break
			obj = obj.leftGuiObject
		while obj:
			yield obj
			obj = getattr(obj, "rightGuiObject", None)

	def layoutLine(self):
		line = list(self.guiObjectsInLine())
		minY = min([control.pos[1] for control in line])
		maxH = max([control.size[1] for control in line])
		
		x = self.parent.OuterSpace[0]
		for control in line:
			spaceX = self.parent.DefaultSpace[0]
			if control.attr.spaceX is not None: spaceX = control.attr.spaceX

			w,h = control.size
			y = minY + (maxH - h) / 2
			
			control.pos = (x,y)
			control.size = (w,h)
			
			x += w + spaceX

		varWidthControl = None
		for control in line:
			if control.attr.variableWidth:
				varWidthControl = control
				break
		if not varWidthControl:
			varWidthControl = line[-1]
		x = self.parent.innerSize[0] - self.parent.OuterSpace[0]
		for control in reversed(line):
			w,h = control.size
			y = control.pos[1]
	
			if control is varWidthControl:
				w = x - control.pos[0]
				x = control.pos[0]
				control.pos = (x,y)
				control.size = (w,h)
				control.autoresize = (False,False,True,False)
				break
			else:
				x -= w
				control.pos = (x,y)
				control.size = (w,h)
				control.autoresize = (True,False,False,False)
				x -= self.parent.DefaultSpace[0]
		
	
	firstChildGuiObject = None
	childs = {} # (attrName -> guiObject) map. this might change...
	def setupChilds(self):
		"If this is a container (a generic object), this does the layouting of the childs"

		self.firstChildGuiObject = None
		self.childs = {}
		x, y = self.OuterSpace
		maxX, maxY = 0, 0
		lastControl = None
		lastVertControls = []
		
		def finishLastHoriz():
			if not lastControl: return
			lastControl.layoutLine()

		def finishLastVert():
			if not lastControl: return
			varHeightControl = None
			for control in lastVertControls:
				if control.attr.variableHeight:
					varHeightControl = control
					break
			if not varHeightControl:
				varHeightControl = lastControl
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
					break
				else:
					y -= h
					control.pos = (x,y)
					control.size = (w,h)
					control.autoresize = control.autoresize[0:1] + (True,) + control.autoresize[2:4]
					y -= self.DefaultSpace[1]
		
		for attr in iterUserAttribs(self.subjectObject):
			control = buildControl(attr, self.subjectObject)
			control.parent = self
			control.attr = attr
			if not self.firstChildGuiObject:
				self.firstChildGuiObject = control
			self.addChild(control)
			self.childs[attr.name] = control
			
			spaceX, spaceY = self.DefaultSpace
			if attr.spaceX is not None: spaceX = attr.spaceX
			if attr.spaceY is not None: spaceY = attr.spaceY
			
			if attr.alignRight and lastControl: # align next right
				x = lastControl.pos[0] + lastControl.size[0] + spaceX
				# y from before
				w,h = control.size # default
				control.leftGuiObject = lastControl
				if lastControl:
					lastControl.rightGuiObject = control
				
			else: # align next below
				finishLastHoriz()
				x = self.OuterSpace[0]
				y = maxY + spaceY
				w,h = control.size # default
				control.topGuiObject = lastControl
				if lastControl:
					lastControl.bottomGuiObject = control
				
			control.pos = (x,y)
			control.size = (w,h)
		
			lastControl = control
			lastVertControls += [control]
			maxX = max(maxX, control.pos[0] + control.size[0])
			maxY = max(maxY, control.pos[1] + control.size[1])
		
			control.updateContent(None,None,None)
				
		finishLastHoriz()
		finishLastVert()
		
		# Handy for now. This return might change.
		return (maxX + self.OuterSpace[0], maxY + self.OuterSpace[1])
	
