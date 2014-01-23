
#import "Builders.hpp"
#import "ListControl.hpp"
#import "PythonHelpers.h"



bool buildControlList(CocoaGuiObject* control) {
	ListControlView* view = [[ListControlView alloc] initWithFrame:NSMakeRect(0, 0, 80, 80) withControl:control];
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
	PyObject* guiCocoaMod = getModule("guiCocoa"); // borrowed ref
	if(!guiCocoaMod) {
		printf("cannot get module guiCocoa\n");
		if(PyErr_Occurred()) PyErr_Print();
		return false;
	}
	Py_INCREF(guiCocoaMod);

	bool success = true;
	PyObject* res = PyObject_CallMethod(guiCocoaMod, (char*)"_buildControlObject_pre", (char*)"(O)", control);
	if(!res) {
		printf("failed to call _buildControlObject_pre\n");
		if(PyErr_Occurred()) PyErr_Print();
		success = false;
	}
	Py_XDECREF(res);
	Py_DECREF(guiCocoaMod);
	return success;
}

bool _buildControlObject_post(CocoaGuiObject* control) {
	PyObject* guiCocoaMod = getModule("guiCocoa"); // borrowed ref
	if(!guiCocoaMod) {
		printf("cannot get module guiCocoa\n");
		if(PyErr_Occurred()) PyErr_Print();
		return false;
	}
	Py_INCREF(guiCocoaMod);
	
	bool success = true;
	PyObject* res = PyObject_CallMethod(guiCocoaMod, (char*)"_buildControlObject_post", (char*)"(O)", control);
	if(!res) {
		printf("failed to call _buildControlObject_post\n");
		if(PyErr_Occurred()) PyErr_Print();
		success = false;
	}
	Py_XDECREF(res);
	Py_DECREF(guiCocoaMod);
	return success;
}
