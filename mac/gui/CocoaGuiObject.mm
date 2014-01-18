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
	GuiObject::init(args, kwds);
	get_pos = imp_get_pos;
	get_size = imp_get_size;
	get_innerSize = imp_get_innnerSize;
	get_autoresize = imp_get_autoresize;
	set_pos = imp_set_pos;
	set_size = imp_set_size;
	set_autoresize = imp_set_autoresize;
	return 0;
}

PyObject* CocoaGuiObject::getattr(const char* key) {
	// fallthrough for now
	return GuiObject::getattr(key);
}

int CocoaGuiObject::setattr(const char* key, PyObject* value) {
	// fallthrough for now
	return GuiObject::setattr(key, value);
}
