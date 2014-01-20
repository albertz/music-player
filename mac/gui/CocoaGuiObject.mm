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
	NSView* view = ((CocoaGuiObject*) obj)->getNativeObj();
	if(!view) return Vec();
	__block CGPoint pos;
	runOnMainQueue(^{
		pos = [view frame].origin;
	});
	return Vec((int)pos.x, (int)pos.y);
}

static Vec imp_get_size(GuiObject* obj) {
	NSView* view = ((CocoaGuiObject*) obj)->getNativeObj();
	if(!view) return Vec();
	__block CGSize size;
	runOnMainQueue(^{
		size = [view frame].size;
	});
	return Vec((int)size.width, (int)size.height);
}

static Vec imp_get_innnerSize(GuiObject* obj) {
	NSView* view = ((CocoaGuiObject*) obj)->getNativeObj();
	if(!view) return Vec();
	__block CGSize size;
	runOnMainQueue(^{
		size = [view bounds].size;
	});
	return Vec((int)size.width, (int)size.height);
}

static Autoresize imp_get_autoresize(GuiObject* obj) {
	NSView* view = ((CocoaGuiObject*) obj)->getNativeObj();
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
	NSView* view = ((CocoaGuiObject*) obj)->getNativeObj();
	if(!view) return;
	runOnMainQueue(^{
		[view setFrameOrigin:NSMakePoint(v.x, v.y)];
	});
}

static void imp_set_size(GuiObject* obj, const Vec& v) {
	NSView* view = ((CocoaGuiObject*) obj)->getNativeObj();
	if(!view) return;
	runOnMainQueue(^{
		[view setFrameSize:NSMakeSize(v.x, v.y)];
	});
}

static void imp_set_autoresize(GuiObject* obj, const Autoresize& r) {
	NSView* view = ((CocoaGuiObject*) obj)->getNativeObj();
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
	if(!PyType_IsSubtype(Py_TYPE(child), &CocoaGuiObject_Type)) {
		PyErr_Format(PyExc_ValueError, "CocoaGuiObject.addChild: we expect a CocoaGuiObject");
		return;
	}

	NSView* childView = ((CocoaGuiObject*) child)->getNativeObj();
	if(!childView) return;
	((CocoaGuiObject*) obj)->addChild(childView);
}

NSView* CocoaGuiObject::getNativeObj() {
	// This function can be called without the Python GIL.
	id nativeObj = nil;
	nativeGuiObject.operate<void>([&](PyObject* ptr) { nativeObj = PyObjCObj_GetNativeObj(ptr); });
	return nativeObj;
}

void CocoaGuiObject::addChild(NSView* child) {
	NSView* view = getNativeObj();
	if(!view) return;
	runOnMainQueue(^{
		[view addSubview:child];
	});
}


int CocoaGuiObject::init(PyObject* args, PyObject* kwds) {
	PyTypeObject* const selfType = &CocoaGuiObject_Type;
	PyObject* base = (PyObject*) selfType->tp_base;
	if(base == (PyObject*) &PyBaseObject_Type) base = NULL;
	
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
	
		((PyTypeObject*) base)->tp_init((PyObject*) this, args, kwds);

		// Set our base.
		// Note that we must call base->tp_init before because
		// _gui.GuiObject.tp_init will also dynamically set its base.
		// This is important so that we get a correct mro here.
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
			Py_FatalError("Can't initialize CocoaGuiObject type");
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
