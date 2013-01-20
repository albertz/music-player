import sys, os

try:
	from PyQt4 import QtGui, QtCore
except ImportError:
	print "Cant load PyQt4"
	raise # That's fatal

from utils import *
import Traits

try:
	app
except NameError: # only declare if not yet declared
	app = None

def setupAfterAppFinishedLaunching():
	setupMainWindow()
	# app.updateWindows()
	print "setupAfterAppFinishedLaunching ready"
		
def getWindow(name):
	global windows
	if windows.get(name, None):
		return windows[name].nativeGuiObject
	return None

def quit():
	app.exit(None)

def setup():
	mydir = os.path.dirname(__file__)
	icon = QtGui.QIcon(mydir + '/icon.svg')
	if not icon:
		print "Cant load icon file"
	else:
		app.setWindowIcon(icon)

def buildControlAction(control):
	button = QtGui.QPushButton()
	actionTarget = ButtonActionHandler().initWithArgs(control.attr, control.parent.subjectObject)
	control.buttonActionHandler = actionTarget # keep ref here. button.target() is only a weakref
	# button.setTarget_(actionTarget)
	def do_update():
		button.setText(control.attr.name.decode("utf-8"))
	do_update()
	button.adjustSize() # to get height
	#button.setFrameSize_((50, button.frame().size.height))

	def update(ev = None, args = None, kwargs = None):
		# do_in_mainthread(do_update, wait=False)
		do_update()

	control.nativeGuiObject = button
	control.updateContent = update
	return control

def buildControlOneLineText(control):
	label = QtGui.QLineEdit()
	label.setTextMargins(22, 30, 22, 30)
	label.setReadOnly(True)
	control.nativeGuiObject = label
	control.getTextObj = lambda: control.subjectObject
	
	def update(ev = None, args = None, kwargs = None):
		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
		s = "???"
		try:
			labelContent = control.getTextObj()
			s = convertToUnicode(labelContent)
		except Exception:
			sys.excepthook(*sys.exc_info())
		def do_update():
			label.setText(s)
			
			if control.attr.autosizeWidth:
				label.adjustSize()
			
			# if label.onMouseEntered or label.onMouseExited:
			# 	if getattr(label, "trackingRect", None):
			# 		label.removeTrackingRect_(label.trackingRect)	
			# 	label.trackingRect = label.addTrackingRect_owner_userData_assumeInside_(label.bounds(), label, None, False)

		# do_in_mainthread(do_update, wait=False)
		do_update()

	control.updateContent = update
	return control

def buildControlClickableLabel(control):
	buildControlOneLineText(control)
	control.getTextObj = lambda: control.subjectObject(handleClick=False)

	label = control.nativeGuiObject

	def onMouseDown(ev):
		try:
			control.subjectObject(handleClick=True)
		except Exception:
			sys.excepthook(*sys.exc_info())			
		control.parent.updateContent()

	label.onMouseDown = onMouseDown

	return control

def buildControl(userAttr, parent):
	print "buildControl %s - %s" % (userAttr, parent)
	control = QtGuiObject()
	control.parent = parent
	control.attr = userAttr
	control.subjectObject = userAttr.__get__(parent.subjectObject)
	typeName = userAttr.getTypeClass().__name__
	assert userAttr.getTypeClass() is getattr(Traits, typeName)
	buildFuncName = "buildControl" + typeName
	buildFunc = globals().get(buildFuncName, None)
	if buildFunc:
		return buildFunc(control)
	else:
		raise NotImplementedError, "%r not handled yet" % userAttr.type

try:
	windows
except NameError:
	windows = {}

class QtGuiObject(object):
	def __init__(self):
		import gui
		self.__class__.__bases__ = (gui.GuiObject, object)

	nativeGuiObject = None
	widget = None
	grid = None

	@property
	def pos(self):
		pos = self.nativeGuiObject.pos()
		return [pos.x(), pos.y()]

	@pos.setter
	def pos(self, value):
		x, y = value
		self.nativeGuiObject.pos().setX(x)
		self.nativeGuiObject.pos().setY(y)

	@property
	def size(self):
		size = self.nativeGuiObject.baseSize()
		return [size.width(), size.height()]

	@size.setter
	def size(self, value):
		self.nativeGuiObject.resize(value)

	@property
	def innerSize(self):
		return (self.nativeGuiObject.bounds().size.width, self.nativeGuiObject.bounds().size.height)

	@property
	def autoresize(self):
		flags = self.nativeGuiObject.autoresizingMask()
		return (flags & NSViewMinXMargin, flags & NSViewMinYMargin, flags & NSViewWidthSizable, flags & NSViewHeightSizable)
	
	@autoresize.setter
	def autoresize(self, value):
		flags = 0
		if value[0]: flags |= NSViewMinXMargin
		if value[1]: flags |= NSViewMinYMargin
		if value[2]: flags |= NSViewWidthSizable
		if value[3]: flags |= NSViewHeightSizable
		self.nativeGuiObject.setAutoresizingMask_(flags)
		
	def addChild(self, child):
		self.grid.addWidget(child.nativeGuiObject, 0, 0)
		# self.nativeGuiObject.addWidget(child.nativeGuiObject, 0, 0)

def setupWindow(subjectObject, windowName, title, isMainWindow=False):
	# win.show() moves window to the top level
	# if getWindow(windowName):
	# 	getWindow(windowName).makeKeyAndOrderFront_(None)
	# 	return

	win = QtGui.QMainWindow()
	win.setGeometry(200, 500, 400, 600)
	win.setWindowTitle(title)

	window = QtGuiObject()
	window.subjectObject = subjectObject

	window.widget = QtGui.QWidget(win)
	window.grid = QtGui.QGridLayout(window.widget)

	window.nativeGuiObject = win
	window.setupChilds()

	window.widget.setLayout(window.grid)
	win.setCentralWidget(window.widget)

	# win.setMinimumSize(w, h)
	
	win.setVisible(True) # or show() ?
	# win.makeMainWindow()

	global windows
	windows[windowName] = window

def setupMainWindow():
	print "setupMainWindow"
	from State import state
	import appinfo
	setupWindow(state, windowName="mainWindow", title=appinfo.progname, isMainWindow=True)

def setupSearchWindow():
	from Search import search
	setupWindow(search, windowName="searchWindow", title="Search")
	
def locateFile(filename):
	# ws = NSWorkspace.sharedWorkspace()
	# ws.selectFile_inFileViewerRootedAtPath_(filename, None)
	pass

try:
	isReload
except NameError:
	isReload = False
else:
	isReload = True

def reloadModuleHandling():
	print "GUI module reload handler ..."

	app.closeAllWindows()

	global windows
	windows.clear()
	
	# appDelegate = PyAppDelegate.alloc().init()
	# app.setDelegate_(appDelegate)
	# appDelegate.retain()ddd

	try:
	 	setupAfterAppFinishedLaunching()
	except:
	 	sys.excepthook(*sys.exc_info())

def guiMain():
	from State import state
	for ev,args,kwargs in state.updates.read():
		try:
			global windows
			for w in windows.values():
				w.updateContent(ev,args,kwargs)
		except:
			sys.excepthook(*sys.exc_info())

def main():
	global app

	app = QtGui.QApplication(sys.argv)
	setup()

	print "entering GUI main loop"
	app.exec_()

	sys.exit()

if isReload:
	do_in_mainthread(reloadModuleHandling)
