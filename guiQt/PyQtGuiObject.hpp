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
#include "QtBaseWidget.hpp"

extern PyTypeObject QtGuiObject_Type;

struct QtBaseWidget;

// This is the Python GUI object (control object).
// This keeps the same Python interface as the CocoaGuiObject.
// It bases itself on the _gui.GuiObject class in its init.
// The CPython API is defined in PythonInterface.cpp.
// It itself is not the native widget
// - it just has a reference to it in `widget`.
// The base native widget class is QtBaseWidget.

struct PyQtGuiObject : GuiObject {
	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);

	QtBaseWidget::WeakRef widget;
	QtBaseWidget::WeakRef getParentWidget();

	Autoresize autoresize;
	
	void addChild(QtBaseWidget::WeakRef child);
	void updateContent();
};


PyQtGuiObject* guiQt_createControlObject(PyObject* subjectObject);


#endif /* defined(__MusicPlayer__QtGuiObject__) */
