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
#include "IntrusivePtr.hpp"

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

inline void intrusive_ptr_add_ref(PyObject* obj) {
	Py_INCREF(obj);
}

inline void intrusive_ptr_release(PyObject* obj) {
	Py_DECREF(obj);
}


struct GuiObject {
	PyObject_HEAD

	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);
	~GuiObject();
	
	PyObject* root;
	PyObject* parent;
	PyObject* attr;
	PyObject* subjectObject;
	IntrusivePtr<PyObject> nativeGuiObject; // atomic so that we can access without the GIL

	Vec DefaultSpace;
	Vec OuterSpace;
	
	// These are expected to be called without holding the GIL!
	Vec (*get_pos)(GuiObject*);
	Vec (*get_size)(GuiObject*);
	Vec (*get_innerSize)(GuiObject*);
	Autoresize (*get_autoresize)(GuiObject*);
	void (*set_pos)(GuiObject*, const Vec&);
	void (*set_size)(GuiObject*, const Vec&);
	void (*set_autoresize)(GuiObject*, const Autoresize&);
	void (*meth_addChild)(GuiObject*, GuiObject*);
};

#endif
