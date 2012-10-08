
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
		x, y = DefaultSpaceX, DefaultSpaceY
		maxX, maxY = 0, 0
		lastControl = None
		lastHorizControls = []
		
		def finishLastHoriz():
			if not lastControl: return
			varWidthControl = None
			for attr,control in lastHorizControls:
				if attr.variableWidth:
					varWidthControl = control
					break
			if not varWidthControl:
				varWidthControl = lastControl
			x = self.innerSize[0]
			for attr,control in reversed(lastHorizControls):
				w = control.size[0]
				h = control.size[1]
				y = control.pos[1]
		
				if control is varWidthControl:
					w = x - control.pos[0] - DefaultSpaceY
					x = control.pos[0]
					control.pos = (x,y)
					control.size = (w,h)
					control.autoresize = (False,False,True,False)
					break
				else:
					x -= w + DefaultSpaceY
					control.pos = (x,y)
					control.size = (w,h)
					control.autoresize = (True,False,False,False)
		
		def finishLastVert():
			if lastControl:
				h = lastControl.pos[1] + lastControl.size[1] + DefaultSpaceY
		
				# make the last one vertically resizable
				h = self.innerSize[1] - y - DefaultSpaceY
				w = self.innerSize[0] - DefaultSpaceY * 2
				lastControl.pos = (x,y)
				lastControl.size = (w,h)
				lastControl.autoresize = (False,False,True,True)
		
		for attr in iterUserAttribs(self.subjectObject):
			control = buildControl(attr, self.subjectObject)
			control.parent = self
			self.addChild(control)
			self.childs[attr.name] = (attr, control)
			
			spaceX = DefaultSpaceX
			spaceY = DefaultSpaceY
			if attr.spaceX is not None: spaceX = attr.spaceX
			if attr.spaceY is not None: spaceY = attr.spaceY
			
			if attr.alignRight and lastControl: # align next right
				x = lastControl.pos[0] + lastControl.size[0] + spaceX
				# y from before
				w,h = control.size # default
		
			else: # align next below
				finishLastHoriz()
				lastHorizControls = []
				x = spaceX
				y = maxY + spaceY
				w,h = control.size # default
				
			control.pos = (x,y)
			control.size = (w,h)
		
			lastControl = control
			lastHorizControls += [(attr,control)]
			maxX = max(maxX, control.pos[0] + control.size[0])
			maxY = max(maxY, control.pos[1] + control.size[1])
		
			control.updateContent(None,None,None)
				
		finishLastHoriz()
		finishLastVert()
		
		# Handy for now. This return might change.
		return (maxX, maxY)
	
