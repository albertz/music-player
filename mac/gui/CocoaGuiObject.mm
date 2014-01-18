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

int CocoaGuiObject::init(PyObject* args, PyObject* kwds) {
	GuiObject::init(args, kwds);
	get_pos = imp_get_pos;
	get_size = imp_get_size;
	get_innerSize = imp_get_innnerSize;
	get_autoresize = imp_get_autoresize;
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
