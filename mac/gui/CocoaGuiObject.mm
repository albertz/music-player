//
//  CocoaGuiObject.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#include "CocoaGuiObject.hpp"
#include "PyObjCBridge.h"
#include "PythonHelpers.h"

void runOnMainQueue(void (^block)(void)) {
	if([NSThread isMainThread])
		block();
	else
		dispatch_sync(dispatch_get_main_queue(), block);
}

static Vec imp_get_pos(GuiObject* obj) {
	NSView* view = PyObjCObj_GetNativeObj(obj->nativeGuiObject);
	if(!view) return Vec();
	__block CGPoint pos;
	runOnMainQueue(^{
		pos = [view frame].origin;
	});
	return Vec((int)pos.x, (int)pos.y);
}

static Vec imp_get_size(GuiObject* obj) {
	NSView* view = PyObjCObj_GetNativeObj(obj->nativeGuiObject);
	if(!view) return Vec();
	__block CGSize size;
	runOnMainQueue(^{
		size = [view frame].size;
	});
	return Vec((int)size.width, (int)size.height);
}

static Vec imp_get_innnerSize(GuiObject* obj) {
	NSView* view = PyObjCObj_GetNativeObj(obj->nativeGuiObject);
	if(!view) return Vec();
	__block CGSize size;
	runOnMainQueue(^{
		size = [view bounds].size;
	});
	return Vec((int)size.width, (int)size.height);
}

static Autoresize imp_get_autoresize(GuiObject* obj) {
	NSView* view = PyObjCObj_GetNativeObj(obj->nativeGuiObject);
	if(!view) return Autoresize();
	__block NSUInteger flags;
	runOnMainQueue(^{
		flags = [view autoresizingMask];
	});
	Autoresize r;
	r.x = flags & NSViewMinXMargin;
	r.y = flags & NSViewMinYMargin;
	r.w = flags & NSViewWidthSizable;
	r.h = flags & NSViewHeightSizable;
	return r;
}

static void imp_set_pos(GuiObject* obj, const Vec& v) {
	NSView* view = PyObjCObj_GetNativeObj(obj->nativeGuiObject);
	if(!view) return;
	runOnMainQueue(^{
		[view setFrameOrigin:NSMakePoint(v.x, v.y)];
	});
}

static void imp_set_size(GuiObject* obj, const Vec& v) {
	NSView* view = PyObjCObj_GetNativeObj(obj->nativeGuiObject);
	if(!view) return;
	runOnMainQueue(^{
		[view setFrameSize:NSMakeSize(v.x, v.y)];
	});
}

static void imp_set_autoresize(GuiObject* obj, const Autoresize& r) {
	NSView* view = PyObjCObj_GetNativeObj(obj->nativeGuiObject);
	if(!view) return;
	NSUInteger flags = 0;
	if(r.x) flags |= NSViewMinXMargin;
	if(r.y) flags |= NSViewMinYMargin;
	if(r.w) flags |= NSViewWidthSizable;
	if(r.h) flags |= NSViewHeightSizable;
	runOnMainQueue(^{
		[view setAutoresizingMask:flags];
	});
}

static void imp_addChild(GuiObject* obj, GuiObject* child) {
	NSView* childView = PyObjCObj_GetNativeObj(child->nativeGuiObject);
	if(!childView) return;
	((CocoaGuiObject*) obj)->addChild(childView);
}

NSView* CocoaGuiObject::getNativeObj() {
	return PyObjCObj_GetNativeObj(nativeGuiObject);
}

void CocoaGuiObject::addChild(NSView* child) {
	NSView* view = getNativeObj();
	if(!view) return;
	runOnMainQueue(^{
		[view addSubview:child];
	});
}


int CocoaGuiObject::init(PyObject* args, PyObject* kwds) {
	PyObject* base = (PyObject*) Py_TYPE(this)->tp_base;

	// We didn't set _gui.GuiObject as the base yet, so dynamically grab it.
	if(base == NULL) {
		base = modAttrChain("_gui", "GuiObject");
		if(!base || PyErr_Occurred()) {
			if(PyErr_Occurred())
				PyErr_Print();
			Py_FatalError("Cannot get _gui.GuiObject");
		}
		if(!PyType_Check(base))
			Py_FatalError("_gui.GuiObject is not a type.");
	}
	
	((PyTypeObject*) base)->tp_init((PyObject*) this, args, kwds);

	// If the base was not set, set it.
	// Note that we must call base->tp_init earlier because
	// _gui.GuiObject.tp_init will also dynamically set its base.
	// This is important so that we get a correct mro here.
	if(Py_TYPE(this)->tp_base == NULL) {
		uninitTypeObject(&CocoaGuiObject_Type);
		CocoaGuiObject_Type.tp_base = (PyTypeObject*) base;
		if(PyType_Ready(&CocoaGuiObject_Type) < 0)
			Py_FatalError("Can't initialize CocoaGuiObject type");
	}

	get_pos = imp_get_pos;
	get_size = imp_get_size;
	get_innerSize = imp_get_innnerSize;
	get_autoresize = imp_get_autoresize;
	set_pos = imp_set_pos;
	set_size = imp_set_size;
	set_autoresize = imp_set_autoresize;
	meth_addChild = imp_addChild;
	return 0;
}

PyObject* CocoaGuiObject::getattr(const char* key) {
	// fallthrough for now
	return Py_TYPE(this)->tp_base->tp_getattr((PyObject*) this, (char*) key);
}

int CocoaGuiObject::setattr(const char* key, PyObject* value) {
	// fallthrough for now
	return Py_TYPE(this)->tp_base->tp_setattr((PyObject*) this, (char*) key, value);
}
