//
//  OneLineTextControl.mm
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "OneLineTextControl.hpp"

@implementation OneLineTextControlView
{
	PyWeakReference* controlRef;
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

- (PyObject*)getTextObj
{
	CocoaGuiObject* control = [self getControl];
	PyObject* textObj = control ? control->subjectObject : NULL;
	Py_XINCREF(textObj);
	Py_XDECREF(control);
	return textObj;
}


@end
