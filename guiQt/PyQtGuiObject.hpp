//
//  PyQtGuiObject.h
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer__PyQtGuiObject__
#define __MusicPlayer__PyQtGuiObject__

#include <Python.h>
#include <QWidget>
#include <QPointer>
#include "GuiObject.hpp"

extern PyTypeObject QtGuiObject_Type;

struct GuiObjectWidget;


struct PyQtGuiObject : GuiObject {
	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);

	// Note: QPointer is like a weak_ref. The parent widget
	// always owns the pointer.
	// Also note: Every access to it must be in the main thread.
	// There is no way to assure that the widget stays alive
	// while we are in another thread!
	QPointer<GuiObjectWidget> widget;
	GuiObjectWidget* getParentWidget();

	void addChild(GuiObjectWidget* child);
	void updateContent();
};

#endif /* defined(__MusicPlayer__QtGuiObject__) */
