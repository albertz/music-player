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

struct PyQtGuiObject : GuiObject {
	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);

	QtBaseWidget::WeakRef widget;
	QtBaseWidget::WeakRef getParentWidget();

	void addChild(QtBaseWidget::WeakRef child);
	void updateContent();
};

#endif /* defined(__MusicPlayer__QtGuiObject__) */
