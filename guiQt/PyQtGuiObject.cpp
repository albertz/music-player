//
//  PyQtGuiObject.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include "PyQtGuiObject.hpp"
#include "PythonHelpers.h"
#include "PyThreading.hpp"
#include "QtBaseWidget.hpp"
#include "QtApp.hpp"


static Vec imp_get_pos(GuiObject* obj) {
	Vec ret;
	execInMainThread_sync([&]() {
		QtBaseWidget::ScopedRef widget(((PyQtGuiObject*) obj)->widget);
		if(widget) {
			QPoint pos = widget->pos();
			ret.x = pos.x();
			ret.y = pos.y();
		}
	});
	return ret;
}

static Vec imp_get_size(GuiObject* obj) {
	Vec ret;
	execInMainThread_sync([&]() {
		QtBaseWidget::ScopedRef widget(((PyQtGuiObject*) obj)->widget);
		if(widget) {
			QSize size = widget->frameSize();
			ret.x = size.width();
			ret.y = size.height();
		}
	});
	return ret;
}

static Vec imp_get_innnerSize(GuiObject* obj) {
	Vec ret;
	execInMainThread_sync([&]() {
		QtBaseWidget::ScopedRef widget(((PyQtGuiObject*) obj)->widget);
		if(widget) {
			QSize size = widget->size();
			ret.x = size.width();
			ret.y = size.height();
		}
	});
	return ret;
}

static Autoresize imp_get_autoresize(GuiObject* obj) {
	return ((PyQtGuiObject*) obj)->autoresize;
}

static void imp_set_pos(GuiObject* obj, const Vec& v) {
	execInMainThread_sync([&]() {
		QtBaseWidget::ScopedRef widget(((PyQtGuiObject*) obj)->widget);
		if(widget)
			widget->move(v.x, v.y);
	});
}

static void imp_set_size(GuiObject* obj, const Vec& v) {
	execInMainThread_sync([&]() {
		QtBaseWidget::ScopedRef widget(((PyQtGuiObject*) obj)->widget);
		if(widget) {
			QSize s = widget->frameSize() - widget->size();
			widget->resize(v.x - s.width(), v.y - s.height());
		}
	});
}

static void imp_set_autoresize(GuiObject* obj, const Autoresize& r) {
	((PyQtGuiObject*) obj)->autoresize = r;
}

static void imp_addChild(GuiObject* obj, GuiObject* child) {
	if(QtApp::isFork()) {
		printf("PyQtGuiObject::imp_addChild called in fork\n");
		return;
	}

	{
		PyScopedGIL gil;
		if(!PyType_IsSubtype(Py_TYPE(child), &QtGuiObject_Type)) {
			PyErr_Format(PyExc_ValueError, "QtGuiObject.addChild: we expect a QtGuiObject");
			return;
		}
	}
	
	execInMainThread_sync([&]() {
		auto childWidget = ((PyQtGuiObject*) child)->widget;
		((PyQtGuiObject*) obj)->addChild(childWidget);
	});
}

static void imp_meth_updateContent(GuiObject* obj) {
	((PyQtGuiObject*) obj)->updateContent();
}

// Called *with* the Python GIL.
static void imp_meth_childIter(GuiObject* obj, boost::function<void(GuiObject* child, bool& stop)> callback) {
	if(QtApp::isFork())
		// Don't care in the fork about it. We should anyway be very careful
		// when touching Qt GUI objects in a fork.
		return;

	QtBaseWidget::ScopedRef widget(((PyQtGuiObject*) obj)->widget);
	if(!widget.ptr) return;
	widget.ptr->childIter(callback);
}

QtBaseWidget::WeakRef PyQtGuiObject::getParentWidget() {
	if(QtApp::isFork()) {
		printf("PyQtGuiObject::getParentWidget called in fork\n");
		return QtBaseWidget::WeakRef();
	}

	PyScopedGIL gil;
	if(parent == NULL)
		return QtBaseWidget::WeakRef();
	if(PyType_IsSubtype(Py_TYPE(parent), &QtGuiObject_Type))
		return ((PyQtGuiObject*) parent)->widget;
	printf("PyQtGuiObject::getParentWidget: parent type is invalid\n");
	return QtBaseWidget::WeakRef();
}

void PyQtGuiObject::addChild(QtBaseWidget::WeakRef child) {
	if(QtApp::isFork()) {
		printf("PyQtGuiObject::addChild called in fork\n");
		return;
	}
		
	// Must not have the Python GIL.
	execInMainThread_sync([&]() {
		QtBaseWidget::ScopedRef widgetRef(widget);
		if(!widgetRef) return;
		QtBaseWidget::ScopedRef childRef(child);
		if(!childRef) return;
		childRef->setParent(widgetRef.ptr);
	});
}

void PyQtGuiObject::updateContent() {
	// Must not have the Python GIL.
	execInMainThread_sync([&]() {	
		QtBaseWidget::ScopedRef widgetRef(widget);
		if(!widgetRef) return;
		widgetRef->updateContent();
	});
}



int PyQtGuiObject::init(PyObject* args, PyObject* kwds) {
	PyTypeObject* const selfType = &QtGuiObject_Type;
	PyObject* base = (PyObject*) selfType->tp_base;
	if(base == (PyObject*) &PyBaseObject_Type) base = NULL;
	
	// We didn't set _gui.GuiObject as the base yet, so set it.
	if(base == NULL) {
		// We need to grab it dynamically because we don't directly link
		// the GuiObject_Type in here.
		base = modAttrChain("_gui", "GuiObject");
		if(!base || PyErr_Occurred()) {
			if(PyErr_Occurred())
				PyErr_Print();
			Py_FatalError("Cannot get _gui.GuiObject");
		}
		if(!PyType_Check(base))
			Py_FatalError("_gui.GuiObject is not a type.");
	
		// Call the base->tp_init first because GuiObject_Type
		// also dynamically inits its base on the first tp_init.
		// We must have the selfType->base->tp_base correct in order to
		// build up a correct selfType->tp_mro.
		((PyTypeObject*) base)->tp_init((PyObject*) this, args, kwds);

		// Now reinit selfType.
		uninitTypeObject(selfType);
		selfType->tp_base = (PyTypeObject*) base; // overtake ref
		
		// Just to be sure that we correctly inited the GC stuff.
		// Just inherit from our base right now.
		assert(PyType_IS_GC(selfType));
		assert(selfType->tp_traverse == NULL);
		assert(selfType->tp_clear == NULL);
		selfType->tp_traverse = ((PyTypeObject*) base)->tp_traverse;
		selfType->tp_clear = ((PyTypeObject*) base)->tp_clear;
		
		if(PyType_Ready(selfType) < 0)
			Py_FatalError("Can't initialize QtGuiObject type");
	}
	else
		((PyTypeObject*) base)->tp_init((PyObject*) this, args, kwds);

	get_pos = imp_get_pos;
	get_size = imp_get_size;
	get_innerSize = imp_get_innnerSize;
	get_autoresize = imp_get_autoresize;
	set_pos = imp_set_pos;
	set_size = imp_set_size;
	set_autoresize = imp_set_autoresize;
	meth_addChild = imp_addChild;
	meth_updateContent = imp_meth_updateContent;
	meth_childIter = imp_meth_childIter;
	return 0;
}

PyObject* PyQtGuiObject::getattr(const char* key) {
	// fallthrough for now
	return Py_TYPE(this)->tp_base->tp_getattr((PyObject*) this, (char*) key);
}

int PyQtGuiObject::setattr(const char* key, PyObject* value) {
	// fallthrough for now
	return Py_TYPE(this)->tp_base->tp_setattr((PyObject*) this, (char*) key, value);
}


PyQtGuiObject* PyQtGuiObject::getParent() {
	if(!parent) return NULL;
	if(!PyType_IsSubtype(Py_TYPE(parent), &QtGuiObject_Type)) {
		PyErr_Format(PyExc_ValueError, "QtGuiObject.getParent: we expect a QtGuiObject");
		return NULL;
	}
	return (PyQtGuiObject*) parent;
}


PyQtGuiObject* guiQt_createControlObject(PyObject* subjectObject, PyQtGuiObject* parent) {
	assert(subjectObject);
	PyQtGuiObject* control = (PyQtGuiObject*) PyObject_CallFunction((PyObject*) &QtGuiObject_Type, NULL);
	if(!control) return NULL;

	control->subjectObject = subjectObject;
	Py_INCREF(subjectObject);

	if(parent) {
		control->parent = parent;
		Py_INCREF(control->parent);

		control->root = parent->root;
		Py_INCREF(control->root);
	}
	else {
		control->root = control; // we are the root
		Py_INCREF(control->root);
	}

	return control;
}
