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
#include <vector>

@implementation ListControlView
{
// Note that we can keep all Python references only in guiObjectList because that
// is handled in childIter: or otherwise in weakrefs.
// Otherwise, our owner, the CocoaGuiObject.tp_traverse would not find all refs
// and the GC would not cleanup correctly when there are cyclic refs.
	PyWeakReference* controlRef;
	PyWeakReference* subjectListRef;
	std::vector<CocoaGuiObject*> guiObjectList;
	NSScrollView* scrollview;
	NSView* documentView;
	BOOL canHaveFocus;
	BOOL autoScrolldown;
	BOOL outstandingScrollviewUpdate;
	int selectionIndex; // for now, a single index. later maybe a range
	_NSFlippedView* dragCursor;
	PyWeakReference* dragHandlerRef;
	int dragIndex;
}

- (void)clearOwn
{
	if(![NSThread isMainThread]) {
		dispatch_sync(dispatch_get_main_queue(), ^{ [self clearOwn]; });
		return;
	}
	
	std::vector<CocoaGuiObject*> listCopy;
	std::swap(guiObjectList, listCopy);
	for(CocoaGuiObject* subCtr : listCopy) {
		NSView* child = subCtr->getNativeObj();
		if(child) [child removeFromSuperview];
		//		subCtr.obsolete = True
		Py_DECREF(subCtr);
	}
}

- (void)dealloc
{
	PyGILState_STATE gstate = PyGILState_Ensure();
	Py_CLEAR(controlRef);
	Py_CLEAR(subjectListRef);
	Py_CLEAR(dragHandlerRef);
	[self clearOwn];
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

	subjectListRef = NULL;
	outstandingScrollviewUpdate = FALSE;
	selectionIndex = -1;
	dragCursor = nil;
	dragHandlerRef = NULL;
	dragIndex = -1;
	
	{
		PyGILState_STATE gstate = PyGILState_Ensure();

		controlRef = (PyWeakReference*) PyWeakref_NewRef((PyObject*) control, NULL);
		if(!controlRef) {
			printf("Cocoa ListControl: cannot create controlRef\n");
			goto finalPyInit;
		}
		control->OuterSpace = Vec(0,0);

		canHaveFocus = attrChain_bool_default((PyObject*) control, "attr.canHaveFocus", false);
		autoScrolldown = attrChain_bool_default((PyObject*) control, "attr.autoScrolldown", false);
		
		{
			PyObject* handler = attrChain((PyObject*) control, "attr.dragHandler");
			if(!handler) {
				printf("Cocoa ListControl: error while getting control.attr.dragHandler\n");
				if(PyErr_Occurred())
					PyErr_Print();
			}
			if(handler) {
				if(handler != Py_None) {
					dragHandlerRef = (PyWeakReference*) PyWeakref_NewRef(handler, NULL);
					if(!dragHandlerRef) {
						printf("Cocoa ListControl: cannot create dragHandlerRef\n");
						if(PyErr_Occurred())
							PyErr_Print();
					}
				}
				Py_CLEAR(handler);
			}
		}
		
		if(!control->subjectObject) {
			printf("Cocoa ListControl: subjectObject is NULL\n");
		} else {
			subjectListRef = (PyWeakReference*) PyWeakref_NewRef(control->subjectObject, NULL);
			if(!subjectListRef) {
				printf("Cocoa ListControl: cannot create subjectListRef\n");
				goto finalPyInit;
			}
		}
		
	finalPyInit:
		if(PyErr_Occurred()) PyErr_Print();
		PyGILState_Release(gstate);
	}

	if(!controlRef || !subjectListRef) return self;

	if(dragHandlerRef) {
		[self registerForDraggedTypes:@[NSFilenamesPboardType]];
		dragCursor = [[_NSFlippedView alloc] initWithFrame:NSMakeRect(0,0,[scrollview contentSize].width,2)];
		[dragCursor setAutoresizingMask:NSViewWidthSizable];
		[dragCursor setBackgroundColor:[NSColor blackColor]];
		[documentView addSubview:dragCursor];
	}

	// do initial fill in background
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT,0), ^{
		PyGILState_STATE gstate = PyGILState_Ensure();
		
		PyObject* lock = NULL;
		PyObject* lockEnterRes = NULL;
		PyObject* lockExitRes = NULL;
		PyObject* list = NULL;
		std::vector<PyObject*> listCopy;
		
		list = PyWeakref_GET_OBJECT(subjectListRef);
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

		{
			PyObject* listIter = PyObject_GetIter(list);
			if(!listIter) {
				printf("Cocoa ListControl: cannot get iter(list)\n");
				if(PyErr_Occurred())
					PyErr_Print();
				goto finalInitialFill;
			}

			while(true) {
				PyObject* listIterItem = PyIter_Next(listIter);
				if(listIterItem == NULL) break;
				listCopy.push_back(listIterItem);
			}

			if(PyErr_Occurred()) {
				printf("Cocoa ListControl: error while copying list\n");
				PyErr_Print();
			}
			Py_DECREF(listIter);
		}
		
		{
			Py_BEGIN_ALLOW_THREADS
			const int Step = 5;
			for(int i = 0; i < listCopy.size(); i += Step) {
				dispatch_sync(dispatch_get_main_queue(), ^{
					for(int j = i; j < listCopy.size() && j < i + Step; ++j) {
						PyGILState_STATE gstate = PyGILState_Ensure();
						CocoaGuiObject* subCtr = [self buildControlForIndex:j andValue:listCopy[j]];
						if(subCtr) guiObjectList.push_back(subCtr);
						PyGILState_Release(gstate);
						[self scrollviewUpdate];
					}
				});
			}
			Py_END_ALLOW_THREADS
		}
		
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
			// Note that in PyObjCPointerWrapper_Init, we PyObjCPointerWrapper_Register the (PyObject*) type,
			// and NSBlock's are supported by PyObjC, so this should hopefully work.
			// The call is handled via PyObjCBlock_Call and the Python GIL is released in it.
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
		for(PyObject* listItem : listCopy)
			Py_DECREF(listItem);
		listCopy.clear();
		
		PyGILState_Release(gstate);
	});
		
    return self;
}

// Callback for subjectObject.
- (void)onInsert:(int)index withValue:(PyObject*) value
{
	if(![NSThread isMainThread]) {
		dispatch_sync(dispatch_get_main_queue(), ^{ [self onInsert:index withValue:value]; });
		return;
	}

	PyGILState_STATE gstate = PyGILState_Ensure();

	if(canHaveFocus && selectionIndex >= 0) {
		if(index <= selectionIndex) selectionIndex += 1;
	}
	
	if(index < 0 || index > guiObjectList.size()) {
		printf("Cocoa ListControl onInsert: invalid index %i, size=%zu\n", index, guiObjectList.size());
		index = (int) guiObjectList.size(); // maybe this recovering works...
		assert(index >= 0);
	}
	CocoaGuiObject* subCtr = [self buildControlForIndex:index andValue:value];
	if(subCtr) guiObjectList.insert(guiObjectList.begin() + index, subCtr);
	PyGILState_Release(gstate);
	
	[self scrollviewUpdate];
}

// Callback for subjectObject.
- (void)onRemove:(int)index
{
	if(![NSThread isMainThread]) {
		dispatch_sync(dispatch_get_main_queue(), ^{ [self onRemove:index]; });
		return;
	}
	
	PyGILState_STATE gstate = PyGILState_Ensure();

	if(canHaveFocus && selectionIndex >= 0) {
		if(index < selectionIndex) selectionIndex -= 1;
		else if(index == selectionIndex) [self deselect];
	}

	if(index >= 0 && index < guiObjectList.size()) {
		CocoaGuiObject* subCtr = guiObjectList[index];
		//	subCtr.obsolete = True
		NSView* child = subCtr->getNativeObj();
		if(child) [child removeFromSuperview];
		guiObjectList.erase(guiObjectList.begin() + index);
		Py_DECREF(subCtr);
	}
	PyGILState_Release(gstate);
	
	[self scrollviewUpdate];
}

// Callback for subjectObject.
- (void)onClear
{
	if(![NSThread isMainThread]) {
		dispatch_sync(dispatch_get_main_queue(), ^{ [self onClear]; });
		return;
	}

	PyGILState_STATE gstate = PyGILState_Ensure();
	selectionIndex = -1;
	[self clearOwn];
	PyGILState_Release(gstate);

	[self scrollviewUpdate];
}

- (void)removeInList:(int)index
{
	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject* list = PyWeakref_GET_OBJECT(subjectListRef);
	PyObject* res = NULL;
	if(!list) goto final;
	
	res = PyObject_CallMethod(list, (char*)"remove", (char*)"(i)", index);
	if(!res || PyErr_Occurred()) {
		if(PyErr_Occurred())
			PyErr_Print();
	}
	
final:
	Py_XDECREF(list);
	Py_XDECREF(res);
	PyGILState_Release(gstate);
}

- (void)deselect
{
	if(selectionIndex >= 0 && selectionIndex < guiObjectList.size()) {
		CocoaGuiObject* subCtr = guiObjectList[selectionIndex];
		NSView* childView = subCtr->getNativeObj();
		if(childView && [childView respondsToSelector:@selector(setBackgroundColor:)])
			[childView performSelector:@selector(setBackgroundColor:) withObject:[NSColor textBackgroundColor]];
		selectionIndex = -1;
	}
}

- (void)select:(int)index
{
	[self deselect];
	if(index < 0 || index >= guiObjectList.size())
		return;
	selectionIndex = index;
	
	CocoaGuiObject* subCtr = guiObjectList[index];
	NSView* childView = subCtr->getNativeObj();
	if(childView && [childView respondsToSelector:@selector(setBackgroundColor:)])
		[childView performSelector:@selector(setBackgroundColor:) withObject:[NSColor selectedTextBackgroundColor]];
	
//				# special handling for gui.ctx().curSelectedSong
//				if control.guiObjectList[index].subjectObject.__class__.__name__ == "Song":
//					import gui
//					gui.ctx().curSelectedSong = control.guiObjectList[index].subjectObject

	dispatch_async(dispatch_get_main_queue(), ^{
		if(!childView || ![childView window]) return; // window closed or removed from window in the meantime
		NSRect objFrame = [childView frame];
		NSRect visibleFrame = [[scrollview contentView] documentVisibleRect];
		if(objFrame.origin.y < visibleFrame.origin.y)
			[[scrollview contentView] scrollToPoint:NSMakePoint(0, objFrame.origin.y)];
		else if(objFrame.origin.y + objFrame.size.height > visibleFrame.origin.y + visibleFrame.size.height)
			[[scrollview contentView] scrollToPoint:
			 NSMakePoint(0, objFrame.origin.y + objFrame.size.height - [scrollview contentSize].height)];
		[scrollview reflectScrolledClipView:[scrollview contentView]];
	});
	
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

- (BOOL)acceptsFirstResponder
{
	return canHaveFocus;
}

- (BOOL)becomeFirstResponder
{
	if(![super becomeFirstResponder]) return NO;
	if(selectionIndex < 0)
		[self select:0];
	[self setDrawsFocusRing:YES];
	return YES;
}

- (BOOL)resignFirstResponder
{
	if(![super resignFirstResponder]) return NO;
	[self setDrawsFocusRing:NO];
	return YES;
}

- (void)keyDown:(NSEvent *)ev
{
	if(!canHaveFocus) {
		[super keyDown:ev];
		return;
	}

	bool res = false;
	if([ev keyCode] == 125) { // down
		if(selectionIndex < 0)
			[self select:0];
		else if(selectionIndex < guiObjectList.size() - 1)
			[self select:selectionIndex+1];
		res = true;
	}
	else if([ev keyCode] == 126) { // up
		if(selectionIndex < 0)
			[self select:0];
		else if(selectionIndex > 0)
			[self select:selectionIndex-1];
		res = true;
	}
	else if([ev keyCode] == 0x33) { // delete
		if(selectionIndex >= 0 && selectionIndex < guiObjectList.size()) {
			int idx = selectionIndex;
			if(idx > 0)
				[self select:idx - 1];
			[self removeInList:idx];
			res = true;
		}
	}
	else if([ev keyCode] == 0x75) { // forward delete
		if(selectionIndex >= 0 && selectionIndex < guiObjectList.size()) {
			int idx = selectionIndex;
			if(idx < guiObjectList.size() - 1)
				[self select:idx + 1];
			[self removeInList:idx];
			res = true;
		}
	}

	if(!res)
		[super keyDown:ev];
}

- (void)mouseDown:(NSEvent *)theEvent
{
	if(!canHaveFocus) {
		[super mouseDown:theEvent];
		return;
	}
	
	bool res = false;
	[[self window] makeFirstResponder:self];
	
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
	if(![NSThread isMainThread]) {
		__block CocoaGuiObject* res = NULL;
		dispatch_sync(dispatch_get_main_queue(), ^{ res = [self buildControlForIndex:index andValue:value]; });
		return res;
	}

	assert(value);
	CocoaGuiObject* subCtr = NULL;
	
	CocoaGuiObject* control = (CocoaGuiObject*) PyWeakref_GET_OBJECT(controlRef);
	if(!control)
		// silently fail. we are probably just out-of-scope
		return NULL;
	if(!PyType_IsSubtype(Py_TYPE(control), &CocoaGuiObject_Type)) {
		printf("Cocoa ListControl buildControlForIndex: controlRef got invalid\n");
		return NULL;
	}
	
	subCtr = (CocoaGuiObject*) PyObject_CallObject((PyObject*) &CocoaGuiObject_Type, NULL);
	if(!subCtr) {
		printf("Cocoa ListControl buildControlForIndex: failed to create CocoaGuiObject\n");
		if(PyErr_Occurred()) PyErr_Print();
		return NULL;
	}
	if(!PyType_IsSubtype(Py_TYPE(subCtr), &CocoaGuiObject_Type)) {
		printf("Cocoa ListControl buildControlForIndex: CocoaGuiObject created unexpected object\n");
		Py_DECREF(subCtr);
		return NULL;
	}

	subCtr->subjectObject = value;
	Py_INCREF(value);
		
	subCtr->root = control->root;
	Py_XINCREF(control->root);
	
	subCtr->parent = (PyObject*) control;
	Py_INCREF(control);

	PyObject* guiMod = getModule("gui"); // borrowed ref
	if(!guiMod) {
		printf("Cocoa ListControl buildControlForIndex: cannot get module gui\n");
		if(PyErr_Occurred()) PyErr_Print();
		Py_DECREF(subCtr);
		return NULL;
	}
	Py_INCREF(guiMod);

	{
		PyObject* res = PyObject_CallMethod(guiMod, (char*)"ListItem_AttrWrapper", (char*)"(iOO)", index, value, control);
		if(!res) {
			printf("Cocoa ListControl buildControlForIndex: cannot create ListItem_AttrWrapper\n");
			if(PyErr_Occurred()) PyErr_Print();
			Py_DECREF(subCtr);
			return NULL;
		}
		subCtr->attr = res; // overtake
	}

	Vec presetSizeVec([scrollview contentSize].width, 80);
	if(!guiObjectList.empty())
		presetSizeVec.y = guiObjectList[0]->get_size(guiObjectList[0]).y;
	{
		PyObject* presetSize = presetSizeVec.asPyObject();
		if(!presetSize) {
			printf("Cocoa ListControl buildControlForIndex: failed to create presetSize\n");
			if(PyErr_Occurred()) PyErr_Print();
			Py_DECREF(subCtr);
			return NULL;
		}
		int res = PyObject_SetAttrString((PyObject*) subCtr, "presetSize", presetSize);
		Py_DECREF(presetSize);
		if(res != 0) {
			printf("Cocoa ListControl buildControlForIndex: failed to set subCtr.presetSize\n");
			if(PyErr_Occurred()) PyErr_Print();
			Py_DECREF(subCtr);
			return NULL;
		}
	}

	{
		PyObject* res = PyObject_CallMethod(guiMod, (char*)"_buildControlObject_pre", (char*)"(O)", subCtr);
		if(!res) {
			printf("Cocoa ListControl buildControlForIndex: failed to call _buildControlObject_pre\n");
			if(PyErr_Occurred()) PyErr_Print();
			Py_DECREF(subCtr);
			return NULL;
		}
		Py_DECREF(res);
	}
	
	NSView* childView = subCtr->getNativeObj();
	if(!childView) {
		printf("Cocoa ListControl buildControlForIndex: subCtr.nativeGuiObject is nil\n");
		Py_DECREF(subCtr);
		return NULL;
	}
	[childView setAutoresizingMask:NSViewWidthSizable];
	// Move out of view so that there isn't any flickering while be lazily build this up.
	[childView setFrameOrigin:NSMakePoint(0, -[childView frame].size.height)];
	if(childView && [childView isKindOfClass:[_NSFlippedView class]])
		[(_NSFlippedView*)childView setDrawsBackground:YES];


	// do subCtr setup in background
	Py_INCREF(subCtr);
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT,0), ^{
		PyGILState_STATE gstate = PyGILState_Ensure();
		
		NSView* childView = nil;
		PyObject* size = NULL;
		Vec sizeVec;
		CocoaGuiObject* control = (CocoaGuiObject*) PyWeakref_GET_OBJECT(controlRef);
		if(!control) goto final; // silently fail. probably out-of-scope
		if(!PyType_IsSubtype(Py_TYPE(control), &CocoaGuiObject_Type)) {
			printf("Cocoa ListControl buildControlForIndex: controlRef got invalid\n");
			goto final;
		}

		childView = subCtr->getNativeObj();
		if(!childView) goto final; // silently fail. probably out-of-scope
		if(![childView window]) goto final; // window was closed

		//	if getattr(subCtr, "obsolete", False): return # can happen in the meanwhile

		size = PyObject_CallMethod((PyObject*) subCtr, (char*)"setupChilds", NULL);
		if(!size) {
			printf("Cocoa ListControl buildControlForIndex: subCtr.setupChilds() failed\n");
			if(PyErr_Occurred()) PyErr_Print();
			goto final;
		}
		if(!sizeVec.initFromPyObject(size)) {
			printf("Cocoa ListControl buildControlForIndex: subCtr.setupChilds() returned unexpected value (expected is tuple (w,h))\n");
			if(PyErr_Occurred()) PyErr_Print();
			goto final;
		}
		
		{
			dispatch_async(dispatch_get_main_queue(), ^{
				int w = [scrollview contentSize].width;
				int h = sizeVec.y;
				[childView setFrameSize:NSMakeSize(w, h)];
			});

			Py_INCREF(subCtr);
			dispatch_async(dispatch_get_main_queue(), ^{
				PyGILState_STATE gstate = PyGILState_Ensure();
				PyObject* guiMod = getModule("gui"); // borrowed ref
				if(!guiMod)
					printf("Cocoa ListControl buildControlForIndex: cannot get module gui\n");
				else {
					PyObject* res = PyObject_CallMethod(guiMod, (char*)"_buildControlObject_post", (char*)"(O)", subCtr);
					if(!res)
						printf("Cocoa ListControl buildControlForIndex: failed to call _buildControlObject_pre\n");
					else Py_DECREF(res);
				}
				if(PyErr_Occurred()) PyErr_Print();
				Py_DECREF(subCtr);
				PyGILState_Release(gstate);
			});

			Py_INCREF(subCtr);
			dispatch_async(dispatch_get_main_queue(), ^{
				PyGILState_STATE gstate = PyGILState_Ensure();
				PyObject* res = PyObject_CallMethod((PyObject*) subCtr, (char*)"updateContent", (char*)"(OOO)", Py_None, Py_None, Py_None);
				if(!res)
					printf("Cocoa ListControl buildControlForIndex: failed to call subCtr.updateContent\n");
				else Py_DECREF(res);
				Py_DECREF(subCtr);
				PyGILState_Release(gstate);
			});

			dispatch_async(dispatch_get_main_queue(), ^{
				// if getattr(subCtr, "obsolete", False): return # can happen in the meanwhile
				[[scrollview documentView] addSubview:childView];
				if(sizeVec.y != presetSizeVec.y)
					[self scrollviewUpdate];
			});
		}
		
	final:
		Py_DECREF(subCtr);
		Py_XDECREF(size);
		PyGILState_Release(gstate);
	});

	Py_DECREF(guiMod);
	return subCtr;
}

@end
