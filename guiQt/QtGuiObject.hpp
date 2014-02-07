//
//  QtGuiObject.h
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer__QtGuiObject__
#define __MusicPlayer__QtGuiObject__

#include <Python.h>
#include <QWidget>
#include "GuiObject.hpp"

extern PyTypeObject QtGuiObject_Type;

struct QtGuiObject : GuiObject {
	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);

	QWidget* getNativeObj(); // This function can be called without the Python GIL.
	void setNativeObj(QWidget* v);
	void addChild(NSView* child);
	void updateContent();
};

#endif /* defined(__MusicPlayer__QtGuiObject__) */
