
#include "Builders.hpp"
#include "QtObjectWidget.hpp"
#include "PythonHelpers.h"
#include <QApplication>
#include <map>
#include <string>

typedef std::map<std::string, ControlBuilderFunc> ControlBuilders;
// Must be lazily inited. Static-init will not work because we might access
// it before it is static-inited.
static ControlBuilders* controlBuilders;

void registerControlBuilder(const std::string& controlType, ControlBuilderFunc buildFunc) {
	if(!controlBuilders) controlBuilders = new ControlBuilders;
	(*controlBuilders)[controlType] = buildFunc;
}

void iterControlTypes(boost::function<void(const std::string&, ControlBuilderFunc)> callback) {
	assert(controlBuilders);
	for(auto& pair : *controlBuilders) {
		callback(pair.first, pair.second);
	}
}

ControlBuilderFunc getControlBuilder(const std::string& controlType) {
	assert(controlBuilders);
	auto it = controlBuilders->find(controlType);
	if(it == controlBuilders->end()) return NULL;
	return it->second;	
}

bool buildControl(const std::string& controlType, PyQtGuiObject* control) {
	assert(controlBuilders);
	auto it = controlBuilders->find(controlType);
	if(it == controlBuilders->end()) {
		printf("Qt buildControl: %s type not found\n", controlType.c_str());
		return false;
	}
	return it->second(control);
}


bool buildControlObject(PyQtGuiObject* control) {
	if(!_buildControlObject_pre(control)) return false;
	
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
	QtBaseWidget::ScopedRef widget(control->widget);
	if(!widget.ptr) return false;
	QColor color = backgroundColor(control);
	if(color.alpha() > 0) {
//		[view setDrawsBackground:YES];
//		[view setBackgroundColor:color];
	}
	return true;
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

