
#include "Builders.hpp"
#include "ListControl.hpp"
#include "ObjectControl.hpp"
#include "OneLineTextControl.hpp"
#include "ClickableLabelControl.hpp"
#include "PythonHelpers.h"



bool buildControlList(QtGuiObject* control) {
	ListControlView* view = [[ListControlView alloc] initWithControl:control];
	control->setNativeObj(view);
	return view != nil;
}


bool buildControlObject(QtGuiObject* control) {
	if(!_buildControlObject_pre(control)) return false;
	
	Vec size = control->setupChilds();
	control->set_size(control, size);
	return _buildControlObject_post(control);
}

bool _buildControlObject_pre(QtGuiObject* control) {
	ObjectControlView* view = [[ObjectControlView alloc] initWithControl:control];
	control->setNativeObj(view);
	return view != nil;
}

static void iterControlParents(GuiObject* control, std::function<bool(GuiObject*)> callback) {
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

QColor backgroundColor(QtGuiObject* control) {
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

QColor foregroundColor(QtGuiObject* control) {
	bool any = false;
	iterControlParents(control, [&](GuiObject* obj) {
		if(attrChain_bool_default(obj->attr, "lowlight", false)) {
			any = true;
			return false;
		}
		return true;
	});
	
	if(any)
		return QApplication::palette().color(Qt::Disabled, Qt::WindowText);
	return QColor(0,0,0);
}

bool _buildControlObject_post(QtGuiObject* control) {
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
}

bool buildControlOneLineText(QtGuiObject* control) {
	OneLineTextControlView* view = [[OneLineTextControlView alloc] initWithControl:control];
	control->setNativeObj(view);
	return view != nil;
}

bool buildControlClickableLabel(QtGuiObject* control) {
	ClickableLabelControlView* view = [[ClickableLabelControlView alloc] initWithControl:control];
	control->setNativeObj(view);
	return view != nil;
}
