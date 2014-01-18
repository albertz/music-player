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

struct Vec {
	int x, y;
	Vec(int _x = 0, int _y = 0) : x(_x), y(_y) {}
	PyObject* asTuple() const;
};

struct GuiObject {
	PyObject_HEAD

	PyObject* root;
	PyObject* parent;
	PyObject* attr;
	PyObject* nativeGuiObject;
	PyObject* subjectObject;

	Vec DefaultSpace;
	Vec OuterSpace;
	
	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);
};

#endif
