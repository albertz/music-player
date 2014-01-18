//
//  CocoaGuiObject.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include "CocoaGuiObject.hpp"

static Vec imp_get_pos(GuiObject*) {
	// TODO
	return Vec();
}

static Vec imp_get_size(GuiObject*) {
	// TODO
	return Vec();
}

static Vec imp_get_innnerSize(GuiObject*) {
	// TODO
	return Vec();
}

static Autoresize imp_get_autoresize(GuiObject*) {
	// TODO
	return Autoresize();
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
