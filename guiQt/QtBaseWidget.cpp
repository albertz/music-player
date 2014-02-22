//
//  GuiObjectView.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include "QtBaseWidget.hpp"
#include "PyQtGuiObject.hpp"
#include "PythonHelpers.h"
#include "PyThreading.hpp"
#include <QThread>
#include <QApplication>

QtBaseWidget::ScopedRef::ScopedRef(const WeakRef& ref) : ptr(NULL), lock(true) {
   _ref = ref.ref.lock();
   if(_ref) {
	   lock = (QThread::currentThread() == qApp->thread());
	   if(lock) _ref->mutex.lock();
	   ptr = _ref->ptr;
   }
}

QtBaseWidget::ScopedRef::~ScopedRef() {
   if(_ref && lock)
	   _ref->mutex.unlock();
}

QtBaseWidget::~QtBaseWidget() {
	selfRef->reset();
	selfRef.reset();
	
	{
		PyScopedGIL gil;
		Py_CLEAR(controlRef);
	}
}

QtBaseWidget::QtBaseWidget(PyQtGuiObject* control) : QWidget(control->getParentWidget().scoped().ptr) {
	selfRef = boost::shared_ptr<LockedRef>(new LockedRef(*this));
	control->widget = QtBaseWidget::WeakRef(*this);	
	
	resize(control->PresetSize.x, control->PresetSize.y);
	
	{
		PyScopedGIL gil;
		controlRef = (PyWeakReference*) PyWeakref_NewRef((PyObject*) control, NULL);
		canHaveFocus = attrChain_bool_default(control->attr, "canHaveFocus", false);
	}
	
	if(!controlRef)
		printf("QtBaseWidget: cannot create controlRef\n");

	if(canHaveFocus)
		this->setFocusPolicy(Qt::StrongFocus);
	else
		this->setFocusPolicy(Qt::NoFocus);
	
	//if(canHaveFocus)
	//	[self setDrawsBackground:YES];
}

PyQtGuiObject* QtBaseWidget::getControl() {
	PyQtGuiObject* control = (PyQtGuiObject*) PyWeakref_GET_OBJECT(controlRef);
	if(!control) return NULL;
	if(!PyType_IsSubtype(Py_TYPE(control), &QtGuiObject_Type)) {
		printf("QtBaseWidget: control is wrong type\n");
		return NULL;
	}
	Py_INCREF(control);
	return control;
}


/*
- (BOOL)becomeFirstResponder
{
	if(![super becomeFirstResponder]) return NO;
	[self setDrawsFocusRing:YES];
	//[self setBackgroundColor:[NSColor selectedTextBackgroundColor]];
	return YES;
}

- (BOOL)resignFirstResponder
{
	if(![super resignFirstResponder]) return NO;
	[self setDrawsFocusRing:NO];
	//[self setBackgroundColor:[NSColor textBackgroundColor]];
	return YES;
}
*/

void QtBaseWidget::mousePressEvent(QMouseEvent* ev) {
	QWidget::mousePressEvent(ev);
	
	PyScopedGIL gil;
	PyQtGuiObject* control = getControl();
	if(control) control->handleCurSelectedSong();
	Py_XDECREF(control);
}

/*
- (void)mouseDragged:(NSEvent *)ev
{
	bool res = false;
	
	PyGILState_STATE gstate = PyGILState_Ensure();
	CocoaGuiObject* control = [self getControl];
	PyObject* subjectObj = control ? control->subjectObject : NULL;
	Py_XINCREF(subjectObj);
	if(control && subjectObj) {
		// For example, if this is a Song object, we have the "url" attrib.
		PyObject* filename = PyObject_GetAttrString(subjectObj, "url");
		if(!filename) {
			if(PyErr_ExceptionMatches(PyExc_AttributeError))
				PyErr_Clear();
			else
				PyErr_Print();
		}
		int ret = filename ? PyObject_IsTrue(filename) : 0;
		if(ret < 0 && PyErr_Occurred())
			PyErr_Print();
		NSString* fn = (ret > 0) ? convertToStr(filename) : nil;
		if(fn) {
			NSPasteboard* pboard = [NSPasteboard pasteboardWithName:NSDragPboard];
			[pboard declareTypes:@[NSFilenamesPboardType] owner:nil];
			[pboard setPropertyList:@[fn] forType:NSFilenamesPboardType];
			NSImage* dragImage = [[NSWorkspace sharedWorkspace] iconForFile:fn];
			NSPoint dragPosition = [self convertPoint:[ev locationInWindow] toView:nil];
			dragPosition.x -= 16;
			dragPosition.y += 32;
			
			[self
			 dragImage:dragImage
			 at:dragPosition
			 offset:NSZeroSize
			 event:ev
			 pasteboard:pboard
			 source:self
			 slideBack:NO];
			
			res = true;
		}
		Py_XDECREF(filename);
	}
	Py_XDECREF(subjectObj);
	Py_XDECREF(control);
	PyGILState_Release(gstate);

	if(!res)
		[super mouseDragged:ev];
}
*/

void QtBaseWidget::updateContent() {	
	PyScopedGIL gil;
	
	PyObject* control = (PyObject*) getControl();
	if(!control) return;
	
	PyObject* s = PyString_FromString("updateContent");
	PyObject* func = s ? PyObject_GenericGetAttr(control, s) : NULL;
	PyObject* res = func ? PyObject_CallFunction(func, NULL) : NULL;
	if(!res && PyErr_Occurred()) PyErr_Print();
	Py_XDECREF(s);
	Py_XDECREF(func);
	Py_XDECREF(res);
	Py_DECREF(control);
}

