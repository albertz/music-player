//
//  GuiObject.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef MusicPlayer_GuiObject_hpp
#define MusicPlayer_GuiObject_hpp

#include <Python.h>

extern PyTypeObject GuiObject_Type;

struct GuiObject {
	PyObject_HEAD

	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);
};

#endif
