
#import "Builders.hpp"
#import "ListControl.hpp"
#import "ObjectControl.hpp"
#import "OneLineTextControl.hpp"
#import "ClickableLabelControl.hpp"
#import "PythonHelpers.h"
#import "PyObjCBridge.h"



bool buildControlList(CocoaGuiObject* control) {
	ListControlView* view = [[ListControlView alloc] initWithControl:control];
	control->setNativeObj(view);
	return view != nil;
}


bool buildControlObject(CocoaGuiObject* control) {
	if(!_buildControlObject_pre(control)) return false;
	
	Vec size = control->setupChilds();
	control->set_size(control, size);
	return _buildControlObject_post(control);
}

bool _buildControlObject_pre(CocoaGuiObject* control) {
	ObjectControlView* view = [[ObjectControlView alloc] initWithControl:control];
	control->setNativeObj(view);
	return view != nil;
}

NSColor* backgroundColor(CocoaGuiObject* control) {
	NSColor* res = nil;
	PyObject* mod = getModule("guiCocoa");
	if(mod) {
		PyObject* colorPy = PyObject_CallMethod(mod, (char*)"backgroundColor", (char*)"(O)", control);
		if(!colorPy && PyErr_Occurred()) PyErr_Print();
		if(colorPy) {
			id _color = PyObjCObj_GetNativeObj(colorPy);
			if(_color && [_color isKindOfClass:[NSColor class]])
				res = (NSColor*) _color;
			Py_DECREF(colorPy);
		}
	}
	return res;
}

NSColor* foregroundColor(CocoaGuiObject* control) {
	NSColor* res = nil;
	PyObject* mod = getModule("guiCocoa");
	if(mod) {
		PyObject* colorPy = PyObject_CallMethod(mod, (char*)"foregroundColor", (char*)"(O)", control);
		if(!colorPy && PyErr_Occurred()) PyErr_Print();
		if(colorPy) {
			id _color = PyObjCObj_GetNativeObj(colorPy);
			if(_color && [_color isKindOfClass:[NSColor class]])
				res = (NSColor*) _color;
			Py_DECREF(colorPy);
		}
	}
	return res;
}

bool _buildControlObject_post(CocoaGuiObject* control) {
	NSView* _view = control->getNativeObj();
	if(!_view || ![_view isKindOfClass:[ObjectControlView class]]) {
		printf("_buildControlObject_post: bad native obj\n");
		return false;
	}
	ObjectControlView* view = (ObjectControlView*) _view;
	NSColor* color = backgroundColor(control);
	if(color) {
		[view setDrawsBackground:YES];
		[view setBackgroundColor:color];
	}	
	return true;
}

bool buildControlOneLineText(CocoaGuiObject* control) {
	long w = attrChain_int_default(control->attr, "width", -1);
	long h = attrChain_int_default(control->attr, "height", -1);
	if(w < 0) w = 30;
	if(h < 0) h = 22;
	control->PresetSize = Vec((int)w, (int)h);

	OneLineTextControlView* view = [[OneLineTextControlView alloc] initWithControl:control];
	control->setNativeObj(view);
	return view != nil;
}

bool buildControlClickableLabel(CocoaGuiObject* control) {
	ClickableLabelControlView* view = [[ClickableLabelControlView alloc] initWithControl:control];
	control->setNativeObj(view);
	return view != nil;
}
