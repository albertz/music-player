//
//  CocoaGuiObject.h
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer__CocoaGuiObject__
#define __MusicPlayer__CocoaGuiObject__

#include <Python.h>
#import <Cocoa/Cocoa.h>
#include "GuiObject.hpp"

extern PyTypeObject CocoaGuiObject_Type;

struct CocoaGuiObject : GuiObject {
	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);

	NSView* getNativeObj(); // This function can be called without the Python GIL.
	void setNativeObj(NSView* v);
	void addChild(NSView* child);
};

#endif /* defined(__MusicPlayer__CocoaGuiObject__) */
