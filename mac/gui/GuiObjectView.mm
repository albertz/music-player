//
//  GuiObjectView.mm
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "GuiObjectView.hpp"

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
	PyGILState_Release(gstate);

	if(!controlRef) {
		printf("Cocoa GuiObject: cannot create controlRef\n");
		return nil;
	}
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

@end
