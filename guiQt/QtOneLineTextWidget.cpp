//
//  QtOneLineTextWidget.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include "QtOneLineTextWidget.hpp"
#include "QtApp.hpp"
#include "Builders.hpp"
#include "PythonHelpers.h"
#include "PyUtils.h"
#include <string>
#include <assert.h>


RegisterControl(OneLineText)

QtOneLineTextWidget::QtOneLineTextWidget(PyQtGuiObject* control) : QtBaseWidget(control) {
	
	PyScopedGIL gil;
	long w = attrChain_int_default(control->attr, "width", -1);
	long h = attrChain_int_default(control->attr, "height", -1);
	if(w < 0) w = 30;
	if(h < 0) h = 22;
	control->PresetSize = Vec((int)w, (int)h);
	resize(w, h);	
	setBaseSize(w, h);
	
	lineEditWidget = new QLineEdit(this);
	lineEditWidget->resize(w, h);
	lineEditWidget->show();
	
	bool withBorder = attrChain_bool_default(control->attr, "withBorder", false);

	lineEditWidget->setFrame(withBorder);
	
	// [self setBordered:NO];
	
	/*
	if(withBorder) {
		[self setBezeled:YES];
		[self setBezelStyle:NSTextFieldRoundedBezel];
	}

	[self setDrawsBackground:NO];
	[[self cell] setUsesSingleLineMode:YES];
	[[self cell] setLineBreakMode:NSLineBreakByTruncatingTail];
	*/

	lineEditWidget->setReadOnly(true);	
}

void QtOneLineTextWidget::resizeEvent(QResizeEvent* ev) {
	QtBaseWidget::resizeEvent(ev);
	lineEditWidget->resize(size());
}

PyObject* QtOneLineTextWidget::getTextObj() {
	PyQtGuiObject* control = getControl();
	PyObject* textObj = control ? control->subjectObject : NULL;
	Py_XINCREF(textObj);
	Py_XDECREF(control);
	return textObj;
}

void QtOneLineTextWidget::updateContent() {
	PyQtGuiObject* control = NULL;
	std::string s = "???";

	{
		PyScopedGIL gil;
	
		control = getControl();
		if(!control) return;
		
		control->updateSubjectObject();
	
		{
			PyObject* labelContent = getTextObj();
			if(!labelContent && PyErr_Occurred()) PyErr_Print();
			if(labelContent) {
				if(!pyStr(labelContent, s)) {
					if(PyErr_Occurred()) PyErr_Print();
				}
			}
		}		
	}

	WeakRef selfRefCopy(*this);
	
	// Note: We had this async before. But I think other code wants to know the actual size
	// and we only get it after we set the text.
	execInMainThread_sync([=]() {
		PyScopedGIL gil;

		ScopedRef selfRef(selfRefCopy);
		if(selfRef) {
			auto self = dynamic_cast<QtOneLineTextWidget*>(selfRef.get());
			assert(self);
			assert(self->lineEditWidget);
			
			self->lineEditWidget->setText(QString::fromStdString(s));
	
			PyScopedGIL gil;
			
			/*
			NSColor* color = backgroundColor(control);
			if(color) {
				[self setDrawsBackground:YES];
				[self setBackgroundColor:color];
			}
			*/
			
			//[self setTextColor:foregroundColor(control)];
			
			bool autosizeWidth = attrChain_bool_default(control->attr, "autosizeWidth", false);
			if(autosizeWidth) {
				QFontMetrics metrics(self->lineEditWidget->fontMetrics());
				int w = metrics.boundingRect(self->lineEditWidget->text()).width();
				w += 5; // TODO: margin size?
				self->resize(w, self->height());
				
				PyObject* res = PyObject_CallMethod((PyObject*) control, (char*)"layoutLine", NULL);
				if(!res && PyErr_Occurred()) PyErr_Print();
				Py_XDECREF(res);
			}
		}
		
		Py_DECREF(control);
	});
}

