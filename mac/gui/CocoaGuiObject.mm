//
//  CocoaGuiObject.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include "CocoaGuiObject.hpp"

int CocoaGuiObject::init(PyObject* args, PyObject* kwds) {
	GuiObject::init(args, kwds);
	return 0;
}

static PyObject* returnAutoresize(const Autoresize& v) {
	PyObject* t = PyTuple_New(4);
	if(!t) return NULL;
	PyTuple_SET_ITEM(t, 0, PyBool_FromLong(v.x));
	PyTuple_SET_ITEM(t, 1, PyBool_FromLong(v.y));
	PyTuple_SET_ITEM(t, 2, PyBool_FromLong(v.w));
	PyTuple_SET_ITEM(t, 3, PyBool_FromLong(v.h));
	return t;
}

PyObject* CocoaGuiObject::getattr(const char* key) {
	if(strcmp(key, "autoresize") == 0) {
		Autoresize r;
		return returnAutoresize(r);
	}

	if(strcmp(key, "pos") == 0) {
		//TODO
	}
	if(strcmp(key, "size") == 0) {
		//TODO
	}
	
	// fallthrough
	return GuiObject::getattr(key);
}

int CocoaGuiObject::setattr(const char* key, PyObject* value) {
	// fallthrough for now
	return GuiObject::setattr(key, value);
}
