//
//  GuiObjectView.mm
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "GuiObjectView.hpp"
#include "PythonHelpers.h"

@implementation GuiObjectView

- (void)dealloc
{
	PyGILState_STATE gstate = PyGILState_Ensure();
	Py_CLEAR(controlRef);
	PyGILState_Release(gstate);
}

- (id)initWithControl:(CocoaGuiObject*)control;
{
	NSRect frame = NSMakeRect(0, 0, control->PresetSize.x, control->PresetSize.y);
    self = [super initWithFrame:frame];
    if(!self) return nil;

	PyGILState_STATE gstate = PyGILState_Ensure();
	controlRef = (PyWeakReference*) PyWeakref_NewRef((PyObject*) control, NULL);
	canHaveFocus = attrChain_bool_default((PyObject*) control, "attr.canHaveFocus", false);
	PyGILState_Release(gstate);

	if(!controlRef) {
		printf("Cocoa GuiObject: cannot create controlRef\n");
		return nil;
	}

	//if(canHaveFocus)
	//	[self setDrawsBackground:YES];

	return self;
}

- (CocoaGuiObject*)getControl;
{
	CocoaGuiObject* control = (CocoaGuiObject*) PyWeakref_GET_OBJECT(controlRef);
	if(!control) return NULL;
	if(!PyType_IsSubtype(Py_TYPE(control), &CocoaGuiObject_Type)) {
		printf("Cocoa GuiObjectView: control is wrong type\n");
		return NULL;
	}
	Py_INCREF(control);
	return control;
}


- (BOOL)acceptsFirstResponder
{
	return canHaveFocus;
}

- (BOOL)becomeFirstResponder
{
	if(![super becomeFirstResponder]) return NO;
	[self setDrawsFocusRing:YES];
	//[self setBackgroundColor:[NSColor selectedTextBackgroundColor]];
	return YES;
}

- (BOOL)resignFirstResponder
{
	if(![super resignFirstResponder]) return NO;
	[self setDrawsFocusRing:NO];
	//[self setBackgroundColor:[NSColor textBackgroundColor]];
	return YES;
}

- (void)mouseDown:(NSEvent *)theEvent
{
	[super mouseDown:theEvent];
	
	PyGILState_STATE gstate = PyGILState_Ensure();
	CocoaGuiObject* control = [self getControl];
	if(control) control->handleCurSelectedSong();
	Py_XDECREF(control);
	PyGILState_Release(gstate);
}

- (void)mouseDragged:(NSEvent *)ev
{
	bool res = false;
	
	PyGILState_STATE gstate = PyGILState_Ensure();
	CocoaGuiObject* control = [self getControl];
	PyObject* subjectObj = control ? control->subjectObject : NULL;
	Py_XINCREF(subjectObj);
	if(control && subjectObj) {
		// For example, if this is a Song object, we have the "url" attrib.
		PyObject* filename = PyObject_GetAttrString(subjectObj, "url");
		if(!filename) {
			if(PyErr_ExceptionMatches(PyExc_AttributeError))
				PyErr_Clear();
			else
				PyErr_Print();
		}
		int ret = filename ? PyObject_IsTrue(filename) : 0;
		if(ret < 0 && PyErr_Occurred())
			PyErr_Print();
		NSString* fn = (ret > 0) ? convertToStr(filename) : nil;
		if(fn) {
			NSPasteboard* pboard = [NSPasteboard pasteboardWithName:NSDragPboard];
			[pboard declareTypes:@[NSFilenamesPboardType] owner:nil];
			[pboard setPropertyList:@[fn] forType:NSFilenamesPboardType];
			NSImage* dragImage = [[NSWorkspace sharedWorkspace] iconForFile:fn];
			NSPoint dragPosition = [self convertPoint:[ev locationInWindow] toView:nil];
			dragPosition.x -= 16;
			dragPosition.y += 32;
			
			[self
			 dragImage:dragImage
			 at:dragPosition
			 offset:NSZeroSize
			 event:ev
			 pasteboard:pboard
			 source:self
			 slideBack:NO];
			
			res = true;
		}
		Py_XDECREF(filename);
	}
	Py_XDECREF(subjectObj);
	Py_XDECREF(control);
	PyGILState_Release(gstate);

	if(!res)
		[super mouseDragged:ev];
}

@end
