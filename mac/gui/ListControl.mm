//
//  ListControl.m
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "ListControl.hpp"
#include "PythonHelpers.h"
#import "PyObjCBridge.h"
#include <list>

@implementation ListControlView
{
	PyWeakReference* subjectList;
	std::list<CocoaGuiObject*> guiObjectList;
	NSScrollView* scrollview;
	NSView* documentView;
	BOOL canHaveFocus;
	BOOL autoScrolldown;
	BOOL outstandingScrollviewUpdate;
	int selectionIndex; // for now, a single index. later maybe a range
	_NSFlippedView* dragCursor;
	PyWeakReference* dragHandler;
	int dragIndex;
}

- (void)dealloc
{
	PyGILState_STATE gstate = PyGILState_Ensure();
	Py_CLEAR(subjectList);
	Py_CLEAR(dragHandler);
	PyGILState_Release(gstate);
}

- (id)initWithFrame:(NSRect)frame withControl:(CocoaGuiObject*)control
{
    self = [super initWithFrame:frame];
    if(!self) return nil;

	scrollview = [[NSScrollView alloc] initWithFrame:frame];
	[scrollview setAutoresizingMask:NSViewWidthSizable|NSViewHeightSizable];
	[[scrollview contentView] setAutoresizingMask:NSViewWidthSizable|NSViewHeightSizable];
	documentView = [[_NSFlippedView alloc] initWithFrame:
					NSMakeRect(0, 0, [scrollview contentSize].width, [scrollview contentSize].height)];
	[scrollview setDocumentView:documentView];
	[documentView setAutoresizingMask:NSViewWidthSizable];
	[scrollview setHasVerticalScroller:YES];
	[scrollview setDrawsBackground:NO];
	[scrollview setBorderType:NSBezelBorder]; // NSGrooveBorder

	[self setAutoresizingMask:NSViewWidthSizable|NSViewHeightSizable];
	[self addSubview:scrollview];
	//view.control = ref(control)

	subjectList = NULL;
	outstandingScrollviewUpdate = FALSE;
	selectionIndex = -1;
	dragCursor = nil;
	dragHandler = NULL;
	dragIndex = -1;
	
	{
		PyGILState_STATE gstate = PyGILState_Ensure();

		control->OuterSpace = Vec(0,0);

		canHaveFocus = attrChain_bool_default((PyObject*) control, "attr.canHaveFocus", false);
		autoScrolldown = attrChain_bool_default((PyObject*) control, "attr.autoScrolldown", false);

		PyObject* handler = attrChain((PyObject*) control, "attr.dragHandler");
		if(!handler)
			printf("Cocoa ListControl: error while getting control.attr.dragHandler\n");
		if(PyErr_Occurred())
			PyErr_Print();
		if(handler) {
			dragHandler = (PyWeakReference*) PyWeakref_NewRef(handler, NULL);
			Py_CLEAR(handler);
		}
		
		if(control->subjectObject)
			subjectList = (PyWeakReference*) PyWeakref_NewRef(control->subjectObject, NULL);
		
		PyGILState_Release(gstate);
	}

	if(!subjectList) {
		printf("Cocoa ListControl: subjectObject is NULL\n");
		return self;
	}

	if(dragHandler) {
		[self registerForDraggedTypes:@[NSFilenamesPboardType]];
		dragCursor = [[_NSFlippedView alloc] initWithFrame:NSMakeRect(0,0,[scrollview contentSize].width,2)];
		[dragCursor setAutoresizingMask:NSViewWidthSizable];
		[dragCursor setBackgroundColor:[NSColor blackColor]];
		[documentView addSubview:dragCursor];
	}

	// do initial fill
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT,0), ^{
		PyGILState_STATE gstate = PyGILState_Ensure();
		
		PyObject* lock = NULL;
		PyObject* lockEnterRes = NULL;
		PyObject* lockExitRes = NULL;
		PyObject* list = NULL;
		
		list = PyWeakref_GET_OBJECT(subjectList);
		if(!list) goto finalInitialFill;
		Py_INCREF(list);
		
		// We must lock the list.lock because we must ensure that we have the
		// data in sync.
		lock = PyObject_GetAttrString(list, "lock");
		if(!lock) {
			printf("Cocoa ListControl: list.lock not found\n");
			if(PyErr_Occurred())
				PyErr_Print();
			goto finalInitialFill;
		}
		
		lockEnterRes = PyObject_CallMethod(lock, (char*)"__enter__", NULL);
		if(!lockEnterRes) {
			printf("Cocoa ListControl: list.lock.__enter__ failed\n");
			if(PyErr_Occurred())
				PyErr_Print();
			goto finalInitialFill;
		}
		
//		import __builtin__
//		listCopy = __builtin__.list(list)
//		
//		control.guiObjectList = []
//		Step = 5
//		def doInitialAddSome(iStart):
//		for i in range(iStart, min(len(listCopy), iStart+Step)):
//			control.guiObjectList += [buildControlForIndex(i, listCopy[i])]
//			updater.update()
//			
//			for i in xrange(0, len(listCopy), Step):
//				do_in_mainthread(lambda: doInitialAddSome(i), wait=True)
		
		
		// We expect the list ( = control->subjectObject ) to support a certain interface,
		// esp. to have onInsert, onRemove and onClear as utils.Event().
		{
			auto registerEv = [=](const char* evName, PyObject* callback /* overtake */) {
				if(!callback) {
					printf("Cocoa ListControl: cannot create list callback for %s\n", evName);
					if(PyErr_Occurred())
						PyErr_Print();
					return;
				}
				PyObject* event = NULL;
				PyObject* res = NULL;
				event = PyObject_GetAttrString(list, evName);
				if(!event) {
					printf("Cocoa ListControl: cannot get list event for %s\n", evName);
					if(PyErr_Occurred())
						PyErr_Print();
					goto finalRegisterEv;
				}
				res = PyObject_CallMethod(event, (char*)"register", (char*)"(O)", callback);
				if(!res) {
					printf("Cocoa ListControl: cannot register list event callback for %s\n", evName);
					if(PyErr_Occurred())
						PyErr_Print();
				}
			finalRegisterEv:
				Py_XDECREF(res);
				Py_XDECREF(event);
				Py_DECREF(callback);
			};
			registerEv("onInsert", PyObjCObj_NewNative(^(int idx, PyObject* v){ [self onInsert:idx withValue:v]; }));
			registerEv("onRemove", PyObjCObj_NewNative(^(int idx){ [self onRemove:idx]; }));
			registerEv("onClear", PyObjCObj_NewNative(^{ [self onClear]; }));
		}
		
		lockExitRes = PyObject_CallMethod(lock, (char*)"__exit__", (char*)"OOO", Py_None, Py_None, Py_None);
		if(!lockExitRes) {
			printf("Cocoa ListControl: list.lock.__exit__ failed\n");
			if(PyErr_Occurred())
				PyErr_Print();
		}

	finalInitialFill:
		Py_XDECREF(lockEnterRes);
		Py_XDECREF(lockExitRes);
		Py_XDECREF(lock);
		Py_XDECREF(list);
		
		PyGILState_Release(gstate);
	});
		
    return self;
}

// Callback for subjectObject.
- (void)onInsert:(int)index withValue:(PyObject*) value
{
	if(canHaveFocus && selectionIndex >= 0) {
		if(index <= selectionIndex) selectionIndex += 1;
	}
		
//	control.guiObjectList.insert(index, buildControlForIndex(index, value))
//	updater.update()

}

// Callback for subjectObject.
- (void)onRemove:(int)index
{
	if(canHaveFocus && selectionIndex >= 0) {
		if(index < selectionIndex) selectionIndex -= 1;
		else if(index == selectionIndex) [self deselect];
	}
	
//	control.guiObjectList[index].obsolete = True
//	control.guiObjectList[index].nativeGuiObject.removeFromSuperview()
//	del control.guiObjectList[index]
//	updater.update()
	
}

// Callback for subjectObject.
- (void)onClear
{
	selectionIndex = -1;
	
//	for subCtr in control.guiObjectList:
//		subCtr.nativeGuiObject.removeFromSuperview()
//		subCtr.obsolete = True
//		del control.guiObjectList[:]
//		updater.update()

}

- (void)deselect
{
//				if self.index is not None:
//					control.guiObjectList[self.index].nativeGuiObject.setBackgroundColor_(AppKit.NSColor.textBackgroundColor())
//					self.index = None
}

- (void)select { [self select:-1]; }

- (void)select:(int)index
{
//				self.deselect()
//				if index is None:
//					if len(control.guiObjectList) == 0: return
//					index = 0
//				self.index = index
//				guiObj = control.guiObjectList[index].nativeGuiObject
//				guiObj.setBackgroundColor_(AppKit.NSColor.selectedTextBackgroundColor())
//				
//				# special handling for gui.ctx().curSelectedSong
//				if control.guiObjectList[index].subjectObject.__class__.__name__ == "Song":
//					import gui
//					gui.ctx().curSelectedSong = control.guiObjectList[index].subjectObject
//				
//				def doScrollUpdate():
//					if not guiObj.window(): return # window closed or removed from window in the meantime
//					objFrame = guiObj.frame()
//					visibleFrame = scrollview.contentView().documentVisibleRect()
//					if objFrame.origin.y < visibleFrame.origin.y:				
//						scrollview.contentView().scrollToPoint_((0, objFrame.origin.y))
//					elif objFrame.origin.y + objFrame.size.height > visibleFrame.origin.y + visibleFrame.size.height:
//						scrollview.contentView().scrollToPoint_((0, objFrame.origin.y + objFrame.size.height - scrollview.contentSize().height))
//					scrollview.reflectScrolledClipView_(scrollview.contentView())
//				do_in_mainthread(doScrollUpdate, wait=False)
	
}

- (void)doScrollviewUpdate
{
	if(!outstandingScrollviewUpdate) return;
	
	__block int x=0, y=0;
	int w = [scrollview contentSize].width;
	[self childIter:^(GuiObject* subCtr, bool& stop) {
		int h = subCtr->get_size(subCtr).y;
		subCtr->set_pos(subCtr, Vec(x,y));
		subCtr->set_size(subCtr, Vec(w,h));
		y += h;
	}];

	[documentView setFrameSize:NSMakeSize(w, y)];

	if(autoScrolldown) {
		[[scrollview verticalScroller] setFloatValue:1];
		[[scrollview contentView] scrollToPoint:
		NSMakePoint(0, [documentView frame].size.height - [scrollview contentSize].height)];
	}
	
	outstandingScrollviewUpdate = NO;
}

- (void)scrollviewUpdate
{
	if(outstandingScrollviewUpdate) return;
	outstandingScrollviewUpdate = YES;
	dispatch_async(dispatch_get_main_queue(), ^{ [self doScrollviewUpdate]; });
}

- (void)drawRect:(NSRect)dirtyRect
{
	[super drawRect:dirtyRect];
	
    // Drawing code here.
}

- (BOOL)acceptsFirstResponder
{
	return canHaveFocus;
}

- (BOOL)becomeFirstResponder
{
	if(![super becomeFirstResponder]) return NO;
	[self select];
	[self setDrawsFocusRing:YES];
	return YES;
}

- (BOOL)resignFirstResponder
{
	if(![super resignFirstResponder]) return NO;
	[self setDrawsFocusRing:NO];
	return YES;
}

- (void)keyDown:(NSEvent *)theEvent
{
	if(!canHaveFocus) {
		[super keyDown:theEvent];
		return;
	}

	bool res = false;
//				# see HIToolbox/Events.h for keycodes
//				if ev.keyCode() == 125: # down
//					if self.index is None:
//						self.select()
//					elif self.index < len(control.guiObjectList) - 1:
//						self.select(self.index + 1)
//					return True
//				elif ev.keyCode() == 126: # up
//					if self.index is None:
//						self.select()
//					elif self.index > 0:
//						self.select(self.index - 1)
//					return True
//				elif ev.keyCode() == 0x33: # delete
//					if self.index is not None:
//						index = self.index
//						if self.index > 0:
//							self.select(self.index - 1)
//						list.remove(index)
//						return True
//				elif ev.keyCode() == 0x75: # forward delete
//					if self.index is not None:
//						index = self.index
//						if self.index < len(control.guiObjectList) - 1:
//							self.select(self.index + 1)
//						list.remove(index)
//						return True

	if(!res)
		[super keyDown:theEvent];
}

- (void)mouseDown:(NSEvent *)theEvent
{
	if(!canHaveFocus) {
		[super mouseDown:theEvent];
		return;
	}
	
	bool res = false;

//				view.window().makeFirstResponder_(view)
//				mouseLoc = scrollview.documentView().convertPoint_toView_(ev.locationInWindow(), None)
//				for index,obj in enumerate(control.guiObjectList):
//					if AppKit.NSPointInRect(mouseLoc, obj.nativeGuiObject.frame()):
//						self.select(index)
//						return True

	
	if(!res)
		[super mouseDown:theEvent];
}

- (BOOL)prepareForDragOperation:(id<NSDraggingInfo>)sender
{
	return YES;
}

- (NSDragOperation)draggingUpdated:(id<NSDraggingInfo>)sender
{
//				self.guiCursor.setDrawsBackground_(True)
//				scrollview.documentView().addSubview_positioned_relativeTo_(self.guiCursor, AppKit.NSWindowAbove, None)
//				dragLoc = scrollview.documentView().convertPoint_toView_(sender.draggingLocation(), None)
//				self.index = 0
//				y = 0
//				for index,obj in enumerate(control.guiObjectList):
//					frame = obj.nativeGuiObject.frame()
//					if dragLoc.y > frame.origin.y + frame.size.height / 2:
//						self.index = index + 1
//						y = frame.origin.y + frame.size.height
//					else:
//						break
//				self.guiCursor.setFrameOrigin_((0,y - 1))
//
//				visibleFrame = scrollview.contentView().documentVisibleRect()
//				mouseLoc = AppKit.NSPoint(dragLoc.x - visibleFrame.origin.x, dragLoc.y - visibleFrame.origin.y)
//				ScrollLimit = 30
//				Limit = 15
//				y = None
//				if mouseLoc.y < Limit:
//					scrollBy = Limit - mouseLoc.y
//					y = visibleFrame.origin.y - scrollBy
//					y = max(y, -ScrollLimit)
//				elif mouseLoc.y > visibleFrame.size.height - Limit:
//					scrollBy = mouseLoc.y - visibleFrame.size.height + Limit
//					y = visibleFrame.origin.y + scrollBy
//					y = min(y, scrollview.documentView().frame().size.height - visibleFrame.size.height + ScrollLimit)
//				if y is not None:
//					scrollview.contentView().scrollToPoint_((0, y))
//					scrollview.reflectScrolledClipView_(scrollview.contentView())

	return NSDragOperationGeneric;
}

- (void)draggingExited:(id<NSDraggingInfo>)sender
{
//				self.guiCursor.setDrawsBackground_(False)
//				self.index = None

}

- (BOOL)performDragOperation:(id<NSDraggingInfo>)sender
{
//				self.guiCursor.setDrawsBackground_(False)
//				import __builtin__
//				try:
//					filenames = __builtin__.list(sender.draggingPasteboard().propertyListForType_(AppKit.NSFilenamesPboardType))
//					filenames = map(convertToUnicode, filenames)
//					index = self.index
//					internalDragCallback = getattr(sender.draggingSource(), "onInternalDrag", None)
//					def doDragHandler():
//						control.attr.dragHandler(
//							control.parent.subjectObject,
//							control.subjectObject,
//							index,
//							filenames)
//						if internalDragCallback:
//							do_in_mainthread(lambda:
//								internalDragCallback(
//									control,
//									index,
//									filenames),
//								wait=False)
//					utils.daemonThreadCall(doDragHandler, name="DragHandler")
//					return True
//				except Exception:
//					sys.excepthook(*sys.exc_info())
//					return False
	return NO;
}

- (void)onInternalDrag:(CocoaGuiObject*)sourceControl withIndex:(int)index withFiles:(NSArray*)filenames
{
//				if sourceControl.parent is control: # internal drag to myself
//					oldIndex = self.index
//					# check if the index is still correct
//					if control.guiObjectList[oldIndex] is sourceControl:
//						self.select(index)
//						list.remove(oldIndex)
	
}

- (void)childIter:(ChildIterCallback)block
{
	for(CocoaGuiObject* child : guiObjectList) {
		bool stop = false;
		block(child, stop);
		if(stop) return;
	}
}

- (CocoaGuiObject*)buildControlForIndex:(int)index andValue:(PyObject*)value {
//		subCtr = CocoaGuiObject()
//		subCtr.subjectObject = value
//		subCtr.root = control.root
//		subCtr.parent = control
//		subCtr.attr = ListItem_AttrWrapper(index, value, control)
//		presetSize = (scrollview.contentSize().width, 80)
//		if len(control.guiObjectList) > 0:
//			presetSize = (presetSize[0], control.guiObjectList[0].size[1])
//		subCtr.presetSize = presetSize
//		_buildControlObject_pre(subCtr)
//		
//		subCtr.autoresize = (False,False,True,False)
//		subCtr.pos = (0,-subCtr.size[1]) # so that there isn't any flickering
//		subCtr.nativeGuiObject.setDrawsBackground_(True)
//
//		def delayedBuild():
//			if control.root.nativeGuiObject.window() is None: return # window was closed
//			if getattr(subCtr, "obsolete", False): return # can happen in the meanwhile
//			
//			w,h = subCtr.setupChilds()			
//			def setSize():
//				w = scrollview.contentSize().width
//				subCtr.size = (w, h)
//			do_in_mainthread(setSize, wait=False)
//			do_in_mainthread(lambda: _buildControlObject_post(subCtr), wait=False)
//			do_in_mainthread(lambda: subCtr.updateContent(None,None,None), wait=False)
//			def addView():
//				if getattr(subCtr, "obsolete", False): return # can happen in the meanwhile
//				scrollview.documentView().addSubview_(subCtr.nativeGuiObject)
//				if h != presetSize[1]:
//					updater.update()
//			do_in_mainthread(addView, wait=False)
//	
//		utils.daemonThreadCall(
//			delayedBuild, name="GUI list item delayed build",
//			queue="GUI-list-item-delayed-build-%i" % (index % 5)
//			)
//		
//		return subCtr

	return NULL;
}

@end
