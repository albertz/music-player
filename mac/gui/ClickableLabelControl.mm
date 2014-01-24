//
//  ClickableLabelControl.mm
//  MusicPlayer
//
//  Created by Albert Zeyer on 24.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "ClickableLabelControl.hpp"

@implementation ClickableLabelControlView

- (id)initWithControl:(CocoaGuiObject*)control
{
    self = [super initWithControl:control];
    if(!self) return nil;
	
	
    return self;
}

- (PyObject*)getTextObj
{
	CocoaGuiObject* control = [self getControl];
	PyObject* subjObj = control ? control->subjectObject : NULL;
	PyObject* textObj = NULL;
	Py_XINCREF(subjObj);
	PyObject* kws = PyDict_New();
	if(subjObj && kws) {
		PyDict_SetItemString(kws, "handleClick", Py_False);
		textObj = PyEval_CallObjectWithKeywords(subjObj, NULL, kws);
	}
	if(PyErr_Occurred()) PyErr_Print();
	Py_XDECREF(kws);
	Py_XDECREF(control);
	return textObj;
}

@end
