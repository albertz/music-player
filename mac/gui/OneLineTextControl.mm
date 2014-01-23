//
//  OneLineTextControl.mm
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "OneLineTextControl.hpp"
#import "PythonHelpers.h"

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

	PyGILState_STATE gstate = PyGILState_Ensure();
	controlRef = (PyWeakReference*) PyWeakref_NewRef((PyObject*) control, NULL);
	bool withBorder = attrChain_bool_default(control->attr, "withBorder", false);
	PyGILState_Release(gstate);

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
	
//		control.subjectObject = control.attr.__get__(control.parent.subjectObject)
//		s = "???"
//		try:
//			labelContent = control.getTextObj()
//			s = convertToUnicode(labelContent)
//		except Exception:
//			sys.excepthook(*sys.exc_info())
//		def do_update():
//			label.setStringValue_(s)
//			
//			if backgroundColor(control):
//				label.setDrawsBackground_(True)
//				label.setBackgroundColor_(backgroundColor(control))
//			label.setTextColor_(foregroundColor(control))
//			
//			if control.attr.autosizeWidth:
//				label.sizeToFit()
//				control.layoutLine()
//			
//			if label.onMouseEntered or label.onMouseExited:
//				if getattr(label, "trackingRect", None):
//					label.removeTrackingRect_(label.trackingRect)	
//				label.trackingRect = label.addTrackingRect_owner_userData_assumeInside_(label.bounds(), label, None, False)
//
//		do_in_mainthread(do_update, wait=False)
	
}

@end
