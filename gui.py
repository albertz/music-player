
import sys

from guiCocoa import *

class GuiObject:
	"This defines the protocol we must support"
	
	parent = None
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
		for attr,obj in self.childs.values():
			if attr.updateHandler:
				try:
					attr.updateHandler(self.subjectObject, attr, ev, args, kwargs)
				except:
					sys.excepthook(*sys.exc_info())
			obj.updateContent(ev, args, kwargs)
	
	childs = {} # (attrName -> attr,guiObject) map. this might change...
	def setupChilds(self):
		"If this is a container (a generic object), this does the layouting of the childs"

		self.childs = {}
		x, y = self.OuterSpace
		maxX, maxY = 0, 0
		lastControl = None
		lastHorizControls = []
		lastVertControls = []
		
		def finishLastHoriz():
			if not lastControl: return
			varWidthControl = None
			for attr,control in lastHorizControls:
				if attr.variableWidth:
					varWidthControl = control
					break
			if not varWidthControl:
				varWidthControl = lastControl
			x = self.innerSize[0] - self.OuterSpace[0]
			for attr,control in reversed(lastHorizControls):
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
					x -= self.DefaultSpace[0]

		def finishLastVert():
			if not lastControl: return
			varHeightControl = None
			for attr,control in lastVertControls:
				if attr.variableHeight:
					varHeightControl = control
					break
			if not varHeightControl:
				varHeightControl = lastControl
			y = self.innerSize[1] - self.OuterSpace[1]
			for attr,control in reversed(lastVertControls):
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
			self.addChild(control)
			self.childs[attr.name] = (attr, control)
			
			spaceX, spaceY = self.DefaultSpace
			if attr.spaceX is not None: spaceX = attr.spaceX
			if attr.spaceY is not None: spaceY = attr.spaceY
			
			if attr.alignRight and lastControl: # align next right
				x = lastControl.pos[0] + lastControl.size[0] + spaceX
				# y from before
				w,h = control.size # default
		
			else: # align next below
				finishLastHoriz()
				lastHorizControls = []
				x = self.OuterSpace[0]
				y = maxY + spaceY
				w,h = control.size # default
				
			control.pos = (x,y)
			control.size = (w,h)
		
			lastControl = control
			lastHorizControls += [(attr,control)]
			lastVertControls += [(attr,control)]
			maxX = max(maxX, control.pos[0] + control.size[0])
			maxY = max(maxY, control.pos[1] + control.size[1])
		
			control.updateContent(None,None,None)
				
		finishLastHoriz()
		finishLastVert()
		
		# Handy for now. This return might change.
		return (maxX + self.OuterSpace[0], maxY + self.OuterSpace[1])
	
