
#include "Builders.hpp"
#include "QtObjectWidget.hpp"
#include "PythonHelpers.h"
#include <QApplication>


bool buildControlObject(PyQtGuiObject* control) {
	if(!_buildControlObject_pre(control)) return false;
	
	Vec size = control->setupChilds();
	control->set_size(control, size);
	return _buildControlObject_post(control);
}

bool _buildControlObject_pre(PyQtGuiObject* control) {
	// TODO...
//	ObjectControlView* view = [[ObjectControlView alloc] initWithControl:control];
//	control->setNativeObj(view);
//	return view != nil;
	return false;
}


bool _buildControlObject_post(PyQtGuiObject* control) {
	// TODO...
/*
	QWidget* _widget = control->getNativeObj();
	if(!_widget || ![_view isKindOfClass:[ObjectControlView class]]) {
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
	*/
	return false;
}


static void iterControlParents(GuiObject* control, boost::function<bool(GuiObject*)> callback) {
	GuiObject* obj = control;
	Py_XINCREF(obj);
	while(obj) {
		if(!callback(obj)) break;
		
		{
			GuiObject* parent = obj->parent;
			Py_XINCREF(parent);
			Py_DECREF(obj);
			obj = parent;
		}
	}
	Py_XDECREF(obj);
}

QColor backgroundColor(PyQtGuiObject* control) {
	bool any = false;
	iterControlParents(control, [&](GuiObject* obj) {
		if(attrChain_bool_default(obj->attr, "highlight", false)) {
			any = true;
			return false;
		}
		return true;
	});
	
	if(any)
		return QColor(0, 0, 255);
	return QColor(0,0,0,0);
}

QColor foregroundColor(PyQtGuiObject* control) {
	bool any = false;
	iterControlParents(control, [&](GuiObject* obj) {
		if(attrChain_bool_default(obj->attr, "lowlight", false)) {
			any = true;
			return false;
		}
		return true;
	});
	
	if(any)
		return QApplication::palette().color(QPalette::Disabled, QPalette::WindowText);
	return QColor(0,0,0);
}
