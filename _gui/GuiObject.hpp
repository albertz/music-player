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
	bool initFromPyObject(PyObject* obj);
	PyObject* asPyObject() const;
};

struct Autoresize {
	bool x,y,w,h;
	Autoresize() : x(false), y(false), w(false), h(false) {}
	bool initFromPyObject(PyObject* obj);
	PyObject* asPyObject() const;
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
	
	Vec (*get_pos)(GuiObject*);
	Vec (*get_size)(GuiObject*);
	Vec (*get_innerSize)(GuiObject*);
	Autoresize (*get_autoresize)(GuiObject*);
	void (*set_pos)(GuiObject*, const Vec&);
	void (*set_size)(GuiObject*, const Vec&);
	void (*set_autoresize)(GuiObject*, const Autoresize&);
	
	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);
};

#endif
