
#include "QtActionWidget.hpp"
#include "Builders.hpp"
#include "PyUtils.h"

RegisterControl(Action)

QtActionWidget::QtActionWidget(PyQtGuiObject* control) : QtBaseWidget(control) {
	resize(50, 25);
	buttonWidget = new QPushButton(this);
	buttonWidget->resize(size());
	buttonWidget->show();
	connect(buttonWidget, SIGNAL(clicked()), this, SLOT(onClick()));
	updateTitle();
}

void QtActionWidget::updateContent() {
	updateTitle();
}

void QtActionWidget::updateTitle() {
	PyScopedGIL gil;
	PyQtGuiObject* control = getControl();
	if(!control) return;
	
	if(control->attr) {
		PyObject* attrName = PyObject_GetAttrString(control->attr, "name");
		if(!attrName) {
			if(PyErr_Occurred()) PyErr_Print();
			return;
		}
		
		std::string name;
		if(!pyStr(attrName, name)) {
			if(PyErr_Occurred()) PyErr_Print();			
		}
		else {
			buttonWidget->setText(QString::fromStdString(name));
		}
		
		Py_DECREF(attrName);
	}
}

void QtActionWidget::resizeEvent(QResizeEvent *) {
	buttonWidget->resize(size());
}

void QtActionWidget::onClick() {
	PyScopedGIL gil;
	PyQtGuiObject* control = getControl();
	if(!control) return;
	control->updateSubjectObject();
	if(control->subjectObject) {
		PyObject* ret = PyObject_CallFunction(control->subjectObject, NULL);
		if(!ret) {
			if(PyErr_Occurred()) PyErr_Print();			
		}
		Py_XDECREF(ret);
	}
}
