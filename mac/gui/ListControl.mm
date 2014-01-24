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
#import "Builders.hpp"
#include "FunctionWrapper.hpp"
#include <vector>
#include <string>



@implementation ListControlView
{
	PyWeakReference* subjectListRef;
	std::vector<CocoaGuiObject*> guiObjectList;
	NSScrollView* scrollview;
	NSView* documentView;
	BOOL autoScrolldown;
	BOOL outstandingScrollviewUpdate;
	int selectionIndex; // for now, a single index. later maybe a range
	_NSFlippedView* dragCursor;
	PyWeakReference* dragHandlerRef;
	int dragIndex;
}

- (void)clearOwn
{
	// We expect to have the Python GIL.
	
	if(![NSThread isMainThread]) {
		Py_BEGIN_ALLOW_THREADS
		dispatch_sync(dispatch_get_main_queue(), ^{
			PyGILState_STATE gstate = PyGILState_Ensure();
			[self clearOwn];
			PyGILState_Release(gstate);
		});
		Py_END_ALLOW_THREADS
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
	Py_CLEAR(subjectListRef);
	Py_CLEAR(dragHandlerRef);
	[self clearOwn];
	PyGILState_Release(gstate);
}

- (id)initWithControl:(CocoaGuiObject*)control
{
    self = [super initWithControl:control];
    if(!self) return nil;

	scrollview = [[NSScrollView alloc] initWithFrame:[self frame]];
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
		
		control->OuterSpace = Vec(0,0);

		autoScrolldown = attrChain_bool_default(control->attr, "autoScrolldown", false);
		
		{
			PyObject* handler = attrChain(control->attr, "dragHandler");
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

	if(!subjectListRef) return nil;

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
				goto unlockInitialFill;
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
			auto registerEv = [=](const char* evName, PyCallback func) {
				CocoaGuiObject* control = NULL;
				PyObject* event = NULL;
				PyObject* res = NULL;
				PyObject* callbackWrapper = NULL;
				
				control = [self getControl];
				if(!control) goto finalRegisterEv;
				
				callbackWrapper = (PyObject*) newFunctionWrapper(func);
				if(!callbackWrapper) {
					printf("Cocoa ListControl: cannot create callback wrapper for %s\n", evName);
					goto finalRegisterEv;
				}
												
				event = PyObject_GetAttrString(list, evName);
				if(!event) {
					printf("Cocoa ListControl: cannot get list event for %s\n", evName);
					goto finalRegisterEv;
				}
				
				res = PyObject_CallMethod(event, (char*)"register", (char*)"(O)", callbackWrapper);
				if(!res) {
					printf("Cocoa ListControl: cannot register list event callback for %s\n", evName);
					goto finalRegisterEv;
				}
				
				// And we assign the wrapper-object to the CocoaGuiObject(control),
				// otherwise there would not be any strong ref to it.
				// We do this as the last step, so that we do it only if we did not fail so far.
				char attribName[255];
				snprintf(attribName, sizeof(attribName), "_%s", evName);
				if(PyObject_SetAttrString((PyObject*) control, attribName, callbackWrapper) != 0) {
					printf("Cocoa ListControl: failed to set %s\n", attribName);
					goto finalRegisterEv;
				}

			finalRegisterEv:
				if(PyErr_Occurred())
					PyErr_Print();
				Py_XDECREF(control);
				Py_XDECREF(res);
				Py_XDECREF(event);
				Py_XDECREF(callbackWrapper);
			};

			registerEv("onInsert", [=](PyObject* args, PyObject* kws) {
				int idx; PyObject* v;
				static const char *kwlist[] = {"index", "value", NULL};
				if(!PyArg_ParseTupleAndKeywords(args, kws, "iO:onInsert", (char**)kwlist, &idx, &v))
					return (PyObject*) NULL;
				[self onInsert:idx withValue:v];
				Py_INCREF(Py_None);
				return Py_None;
			});
			registerEv("onRemove", [=](PyObject* args, PyObject* kws) {
				int idx;
				static const char *kwlist[] = {"index", NULL};
				if(!PyArg_ParseTupleAndKeywords(args, kws, "i:onRemove", (char**)kwlist, &idx))
					return (PyObject*) NULL;
				[self onRemove:idx];
				Py_INCREF(Py_None);
				return Py_None;
			});
			registerEv("onClear", [=](PyObject* args, PyObject* kws) {
				static const char *kwlist[] = {NULL};
				if(!PyArg_ParseTupleAndKeywords(args, kws, ":onClear", (char**)kwlist))
					return (PyObject*) NULL;
				[self onClear];
				Py_INCREF(Py_None);
				return Py_None;
			});
		}
		
	unlockInitialFill:
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
	PyGILState_STATE gstate = PyGILState_Ensure();

	if(![NSThread isMainThread]) {
		Py_BEGIN_ALLOW_THREADS
		dispatch_sync(dispatch_get_main_queue(), ^{ [self onInsert:index withValue:value]; });
		Py_END_ALLOW_THREADS
		return;
	}

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
	PyGILState_STATE gstate = PyGILState_Ensure();

	if(![NSThread isMainThread]) {
		Py_BEGIN_ALLOW_THREADS
		dispatch_sync(dispatch_get_main_queue(), ^{ [self onRemove:index]; });
		Py_END_ALLOW_THREADS
		return;
	}
	
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
	PyGILState_STATE gstate = PyGILState_Ensure();

	if(![NSThread isMainThread]) {
		Py_BEGIN_ALLOW_THREADS
		dispatch_sync(dispatch_get_main_queue(), ^{ [self onClear]; });
		Py_END_ALLOW_THREADS
		return;
	}

	selectionIndex = -1;
	[self clearOwn];
	PyGILState_Release(gstate);

	[self scrollviewUpdate];
}

- (void)removeInList:(int)index
{
	// don't run this in the main thread. it can lock.
	assert(![NSThread isMainThread]);

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

	PyGILState_STATE gstate = PyGILState_Ensure();
	
	if(index >= 0 && index < guiObjectList.size()) {
		selectionIndex = index;
		
		CocoaGuiObject* subCtr = guiObjectList[index];
		NSView* childView = subCtr->getNativeObj();
		if(childView && [childView respondsToSelector:@selector(setBackgroundColor:)])
			[childView performSelector:@selector(setBackgroundColor:) withObject:[NSColor selectedTextBackgroundColor]];
		
		subCtr->handleCurSelectedSong();
		
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
	
	PyGILState_Release(gstate);
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

- (BOOL)becomeFirstResponder
{
	if(![super becomeFirstResponder]) return NO;
	if(selectionIndex < 0)
		[self select:0];
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
			dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT,0), ^{
				[self removeInList:idx];
			});
			res = true;
		}
	}
	else if([ev keyCode] == 0x75) { // forward delete
		if(selectionIndex >= 0 && selectionIndex < guiObjectList.size()) {
			int idx = selectionIndex;
			if(idx < guiObjectList.size() - 1)
				[self select:idx + 1];
			dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT,0), ^{
				[self removeInList:idx];
			});
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
	
	NSPoint mouseLoc = [documentView convertPoint:[theEvent locationInWindow] toView:nil];
	PyGILState_STATE gstate = PyGILState_Ensure();
	for(int i = 0; i < (int)guiObjectList.size(); ++i) {
		if(NSPointInRect(mouseLoc, [guiObjectList[i]->getNativeObj() frame])) {
			[self select:i];
			res = true;
			break;
		}
	}
	PyGILState_Release(gstate);
	
	if(!res)
		[super mouseDown:theEvent];
}

- (BOOL)prepareForDragOperation:(id<NSDraggingInfo>)sender
{
	return YES;
}

- (NSDragOperation)draggingUpdated:(id<NSDraggingInfo>)sender
{
	[dragCursor setDrawsBackground:YES];
	[documentView addSubview:dragCursor positioned:NSWindowAbove relativeTo:nil];
	NSPoint dragLoc = [documentView convertPoint:[sender draggingLocation] toView:nil];
	dragIndex = 0;
	
	CGFloat y = 0;
	PyGILState_STATE gstate = PyGILState_Ensure();
	for(int i = 0; i < (int)guiObjectList.size(); ++i) {
		NSRect frame = [guiObjectList[i]->getNativeObj() frame];
		if(dragLoc.y > frame.origin.y + frame.size.height / 2) {
			dragIndex = i + 1;
			y = frame.origin.y + frame.size.height;
		}
		else break;
	}
	PyGILState_Release(gstate);
	[dragCursor setFrameOrigin:NSMakePoint(0, y-1)];
	
	NSRect visibleFrame = [[scrollview contentView] documentVisibleRect];
	NSPoint mouseLoc = NSMakePoint(dragLoc.x - visibleFrame.origin.x, dragLoc.y - visibleFrame.origin.y);

	const CGFloat ScrollLimit = 30;
	const CGFloat Limit = 15;
	bool scroll = false;
	if(mouseLoc.y < Limit) {
		float scrollBy = Limit - mouseLoc.y;
		y = visibleFrame.origin.y - scrollBy;
		y = std::max(y, -ScrollLimit);
		scroll = true;
	}
	else if(mouseLoc.y > visibleFrame.size.height - Limit) {
		float scrollBy = mouseLoc.y - visibleFrame.size.height + Limit;
		y = visibleFrame.origin.y + scrollBy;
		y = std::min(y, [documentView frame].size.height - visibleFrame.size.height + ScrollLimit);
		scroll = true;
	}
	if(scroll) {
		[[scrollview contentView] scrollToPoint:NSMakePoint(0, y)];
		[scrollview reflectScrolledClipView:[scrollview contentView]];
	}
	
	return NSDragOperationGeneric;
}

- (void)draggingExited:(id<NSDraggingInfo>)sender
{
	if(dragCursor) {
		[dragCursor setDrawsBackground:NO];
		[dragCursor removeFromSuperview];
	}
	dragIndex = -1;
}

- (BOOL)performDragOperation:(id<NSDraggingInfo>)sender
{
	if(dragCursor) {
		[dragCursor setDrawsBackground:NO];
		[dragCursor removeFromSuperview];
	}
	if(!dragHandlerRef) return NO;
	
	id dragSource = [sender draggingSource];
	NSArray* filenames = [[sender draggingPasteboard] propertyListForType:NSFilenamesPboardType];
	int index = dragIndex;
	
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT,0), ^{
		PyGILState_STATE gstate = PyGILState_Ensure();
		PyObject* dragHandler = PyWeakref_GET_OBJECT(dragHandlerRef);
		CocoaGuiObject* control = [self getControl];
		if(dragHandler && control) {
			Py_INCREF(dragHandler);
			Py_INCREF(control);
			CocoaGuiObject* parent = NULL;
			PyObject* res = NULL;
			PyObject* pyFilenames = NULL;

			parent = (CocoaGuiObject*) control->parent;
			if(!parent) {
				printf("Cocoa ListControl performDragOperation: control.parent is unset\n");
				goto finalCall;
			}
			Py_INCREF(parent);
			if(!PyType_IsSubtype(Py_TYPE(parent), &CocoaGuiObject_Type)) {
				printf("Cocoa ListControl performDragOperation: control.parent is wrong type\n");
				goto finalCall;
			}

			if(!control->subjectObject) {
				printf("Cocoa ListControl performDragOperation: control.subjectObject is unset\n");
				goto finalCall;
			}
			if(!parent->subjectObject) {
				printf("Cocoa ListControl performDragOperation: control.parent.subjectObject is unset\n");
				goto finalCall;
			}

			pyFilenames = PyTuple_New([filenames count]);
			if(!pyFilenames) {
				printf("Cocoa ListControl performDragOperation: failed to create pyFilenames\n");
				goto finalCall;
			}
			for(NSUInteger i = 0; i < [filenames count]; ++i) {
				NSString* objcStr = [filenames objectAtIndex:i];
				std::string cppStr([objcStr UTF8String]);
				PyObject* pyStr = PyUnicode_DecodeUTF8(&cppStr[0], cppStr.size(), NULL);
				if(!pyStr) {
					printf("Cocoa ListControl performDragOperation: failed to convert unicode filename\n");
					goto finalCall;
				}
				PyTuple_SET_ITEM(pyFilenames, i, pyStr);
			}

			res = PyObject_CallFunction(dragHandler, (char*)"(OOiO)", parent->subjectObject, control->subjectObject, index, pyFilenames);
			if(!res) {
				printf("Cocoa ListControl performDragOperation: dragHandler failed\n");
				goto finalCall;
			}

			{
				CocoaGuiObject* sourceControl = NULL;
				if([dragSource isKindOfClass:[GuiObjectView class]])
					sourceControl = [(GuiObjectView*)dragSource getControl];
				
				if(sourceControl) {
					GuiObject* parentControl = ((CocoaGuiObject*)sourceControl)->parent;
					Py_XINCREF(parentControl);
					if(parentControl && PyType_IsSubtype(Py_TYPE(parentControl), &CocoaGuiObject_Type)) {
						NSView* parentView = ((CocoaGuiObject*)parentControl)->getNativeObj();
						
						if([parentView isKindOfClass:[ListControlView class]]) {
							Py_INCREF(control);
							Py_INCREF(sourceControl);
							dispatch_async(dispatch_get_main_queue(), ^{
								PyGILState_STATE gstate = PyGILState_Ensure();
								[(ListControlView*)parentView onInternalDrag:control withObject:(CocoaGuiObject*)sourceControl withIndex:index withFiles:filenames];
								Py_DECREF(control);
								Py_DECREF(sourceControl);
								PyGILState_Release(gstate);
							});
						}
					}
					Py_XDECREF(parentControl);
				}
				
				Py_XDECREF(sourceControl);
			}
			
		finalCall:
			if(PyErr_Occurred()) PyErr_Print();
			Py_XDECREF(pyFilenames);
			Py_XDECREF(parent);
			Py_XDECREF(res);
			Py_DECREF(dragHandler);
			Py_DECREF(control);
		}
		Py_XDECREF(control);
		PyGILState_Release(gstate);
	});

	return YES;
}

- (void)onInternalDrag:(CocoaGuiObject*)destControl withObject:(CocoaGuiObject*)obj withIndex:(int)index withFiles:(NSArray*)filenames
{
	PyGILState_STATE gstate = PyGILState_Ensure();

	if(PyWeakref_GET_OBJECT(controlRef) == (PyObject*)destControl) { // internal drag to myself
		int oldIndex = selectionIndex;
		// check if the index is still correct
		if(oldIndex >= 0 && oldIndex < guiObjectList.size() && guiObjectList[oldIndex] == obj) {
			
			[self select:index];
			dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT,0), ^{
				[self removeInList:oldIndex];
			});
		}
	}
	
	PyGILState_Release(gstate);
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
		Py_BEGIN_ALLOW_THREADS
		dispatch_sync(dispatch_get_main_queue(), ^{
			PyGILState_STATE gstate = PyGILState_Ensure();
			res = [self buildControlForIndex:index andValue:value];
			PyGILState_Release(gstate);
		});
		Py_END_ALLOW_THREADS
		return res;
	}

	assert(value);
	CocoaGuiObject* subCtr = NULL;
	
	CocoaGuiObject* control = [self getControl];
	if(!control)
		// silently fail. we are probably just out-of-scope
		return NULL;
	
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
	
	subCtr->parent = control;
	Py_INCREF(control);

	PyObject* guiCocoaMod = getModule("guiCocoa"); // borrowed ref
	if(!guiCocoaMod) {
		printf("Cocoa ListControl buildControlForIndex: cannot get module gui\n");
		if(PyErr_Occurred()) PyErr_Print();
		Py_DECREF(subCtr);
		return NULL;
	}
	Py_INCREF(guiCocoaMod);

	{
		PyObject* res = PyObject_CallMethod(guiCocoaMod, (char*)"ListItem_AttrWrapper", (char*)"(iOO)", index, value, control);
		if(!res) {
			printf("Cocoa ListControl buildControlForIndex: cannot create ListItem_AttrWrapper\n");
			if(PyErr_Occurred()) PyErr_Print();
			Py_DECREF(subCtr);
			return NULL;
		}
		subCtr->attr = res; // overtake
	}

	subCtr->PresetSize.x = [scrollview contentSize].width;
	if(!guiObjectList.empty())
		subCtr->PresetSize.y = guiObjectList[0]->get_size(guiObjectList[0]).y;

	if(!_buildControlObject_pre(subCtr)) {
		Py_DECREF(subCtr);
		return NULL;
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

		NSView* myView = nil;
		NSView* childView = nil;
		Vec sizeVec;
		CocoaGuiObject* control = [self getControl];
		if(!control) goto final; // silently fail. probably out-of-scope

		myView = control->getNativeObj();
		if(!myView) goto final; // silently fail. probably out-of-scope
		if(![myView window]) goto final; // window was closed

		childView = subCtr->getNativeObj();
		if(!childView) goto final; // silently fail. probably out-of-scope

		//	if getattr(subCtr, "obsolete", False): return # can happen in the meanwhile

		sizeVec = subCtr->setupChilds();
		
		{
			dispatch_async(dispatch_get_main_queue(), ^{
				int w = [scrollview contentSize].width;
				int h = sizeVec.y;
				[childView setFrameSize:NSMakeSize(w, h)];
			});

			Py_INCREF(subCtr);
			dispatch_async(dispatch_get_main_queue(), ^{
				PyGILState_STATE gstate = PyGILState_Ensure();
				_buildControlObject_post(subCtr);
				Py_DECREF(subCtr);
				PyGILState_Release(gstate);
			});

			Py_INCREF(subCtr);
			dispatch_async(dispatch_get_main_queue(), ^{
				subCtr->updateContent();
				Py_DECREF(subCtr);
				PyGILState_Release(gstate);
			});

			int w = subCtr->PresetSize.y;
			dispatch_async(dispatch_get_main_queue(), ^{
				// if getattr(subCtr, "obsolete", False): return # can happen in the meanwhile
				[[scrollview documentView] addSubview:childView];
				if(sizeVec.y != w)
					[self scrollviewUpdate];
			});
		}
		
	final:
		Py_DECREF(control);
		Py_DECREF(subCtr);
		PyGILState_Release(gstate);
	});

	Py_DECREF(control);
	Py_DECREF(guiCocoaMod);
	return subCtr;
}

@end
