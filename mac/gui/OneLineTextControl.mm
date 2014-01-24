//
//  OneLineTextControl.mm
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "OneLineTextControl.hpp"
#import "PythonHelpers.h"
#import "Builders.hpp"


@implementation OneLineTextControlView
{
	PyWeakReference* controlRef;
}

- (void)dealloc
{
	PyGILState_STATE gstate = PyGILState_Ensure();
	Py_CLEAR(controlRef);
	PyGILState_Release(gstate);
}

- (id)initWithControl:(CocoaGuiObject*)control
{
	control->PresetSize = Vec(30, 22);
	NSRect frame = NSMakeRect(0, 0, control->PresetSize.x, control->PresetSize.y);
    self = [super initWithFrame:frame];
    if(!self) return nil;

	[self setBordered:NO];
	
	bool withBorder = false;
	{
		PyGILState_STATE gstate = PyGILState_Ensure();
		controlRef = (PyWeakReference*) PyWeakref_NewRef((PyObject*) control, NULL);
		withBorder = attrChain_bool_default(control->attr, "withBorder", false);
		PyGILState_Release(gstate);
	}
	
	if(!controlRef) return nil;

	if(withBorder) {
		[self setBezeled:YES];
		[self setBezelStyle:NSTextFieldRoundedBezel];
	}

	[self setDrawsBackground:NO];
	[self setEditable:NO];
	[[self cell] setUsesSingleLineMode:YES];
	[[self cell] setLineBreakMode:NSLineBreakByTruncatingTail];

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

- (PyObject*)getTextObj
{
	CocoaGuiObject* control = [self getControl];
	PyObject* textObj = control ? control->subjectObject : NULL;
	Py_XINCREF(textObj);
	Py_XDECREF(control);
	return textObj;
}

- (void)updateContent
{
	CocoaGuiObject* control = [self getControl];
	if(!control) return;
	
	if(control->attr && control->parent && control->parent->subjectObject) {
		PyObject* old = NULL;
		std::swap(old, control->subjectObject);
		control->subjectObject = control->attr ?
			PyObject_CallMethod(control->attr, (char*)"__get__", (char*)"(O)", control->parent->subjectObject)
			: NULL;
		Py_CLEAR(old);
	}

	NSString* s = @"???";
	{
		PyObject* labelContent = [self getTextObj];
		if(!labelContent && PyErr_Occurred()) PyErr_Print();
		if(labelContent) {
			NSString* _s = convertToStr(labelContent);
			if(_s) s = _s;
		}
	}
	
	dispatch_async(dispatch_get_main_queue(), ^{
		[self setStringValue:s];

		PyGILState_STATE gstate = PyGILState_Ensure();
		
		NSColor* color = backgroundColor(control);
		if(color) {
			[self setDrawsBackground:YES];
			[self setBackgroundColor:color];
		}
		
		[self setTextColor:foregroundColor(control)];
		
		bool autosizeWidth = attrChain_bool_default(control->attr, "autosizeWidth", false);
		if(autosizeWidth) {
			[self sizeToFit];
			PyObject* res = PyObject_CallMethod((PyObject*) control, (char*)"layoutLine", NULL);
			if(!res && PyErr_Occurred()) PyErr_Print();
			Py_XDECREF(res);
		}

		//[self removeTrackingRect:];
		//[self addTrackingRect: owner: userData: assumeInside:]
		
		//			if label.onMouseEntered or label.onMouseExited:
		//				if getattr(label, "trackingRect", None):
		//					label.removeTrackingRect_(label.trackingRect)
		//				label.trackingRect = label.addTrackingRect_owner_userData_assumeInside_(label.bounds(), label, None, False)
		
		Py_DECREF(control);
		PyGILState_Release(gstate);
	});
}

@end
