
#import "Builders.hpp"
#import "ListControl.hpp"
#import "ObjectControl.hpp"
#import "OneLineTextControl.hpp"
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

bool _buildControlObject_post(CocoaGuiObject* control) {
	NSView* _view = control->getNativeObj();
	if(!_view || ![_view isKindOfClass:[ObjectControlView class]]) {
		printf("_buildControlObject_post: bad native obj\n");
		return false;
	}
	ObjectControlView* view = (ObjectControlView*) _view;
	PyObject* mod = getModule("guiCocoa");
	if(mod) {
		PyObject* colorPy = PyObject_CallMethod(mod, (char*)"backgroundColor", (char*)"(O)", control);
		if(!colorPy && PyErr_Occurred()) PyErr_Print();
		if(colorPy) {
			NSColor* color = PyObjCObj_GetNativeObj(colorPy);
			if(color && [color isKindOfClass:[NSColor class]]) {
				[view setDrawsBackground:YES];
				[view setBackgroundColor:color];
			}
			Py_DECREF(colorPy);
		}
	}
	
	return true;
}

bool buildControlOneLineText(CocoaGuiObject* control) {
	OneLineTextControlView* view = [[OneLineTextControlView alloc] initWithControl:control];
	control->setNativeObj(view);
	return view != nil;
}
