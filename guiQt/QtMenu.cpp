

#include "QtMenu.hpp"
#include "QtApp.hpp"
#include "PyThreading.hpp"
#include "PythonHelpers.h"
#include "PyUtils.h"
#include <QMenuBar>

QMenuBar* mainMenuBar = NULL;

static void iterRootObjs(QMenu* parent) {
	PyScopedGIL gil;
	
	PyObject* guiMod = getModule("gui"); // borrowed
	if(!guiMod) {
		printf("Qt setupMenu: gui mod not found\n");
		return;
	}
	
	PyObject* rootObjs = PyObject_CallMethod(guiMod, "iterRootObjs", NULL);
	if(!rootObjs) {
		printf("gui.iterRootObjs failed\n");
		if(PyErr_Occurred()) PyErr_Print();
		return;
	}
	
	PyObject* rootObjIter = PyObject_GetIter(rootObjs);
	if(!rootObjIter) {
		printf("gui.iterRootObjs iter failed\n");
		if(PyErr_Occurred()) PyErr_Print();
		Py_DECREF(rootObjs);
		return;
	}
	
	while(PyObject* item = PyIter_Next(rootObjIter)) {
		PyObject* nameObj = PyObject_GetAttrString(item, "name");
		std::string name;
		if(!nameObj || !pyStr(nameObj, name)) {
			printf("Qt iterRootObjs: cannot get name\n");
			if(PyErr_Occurred()) PyErr_Print();			
		}
		else {
			QAction* act = parent->addAction(QString::fromStdString(name + " window"), QtApp::instance(), SLOT(openWindowViaMenu()));
			if(act) act->setObjectName(QString::fromStdString(name));
		}
		Py_XDECREF(nameObj);
	    Py_DECREF(item);
	}
	
	Py_DECREF(rootObjIter);
	Py_DECREF(rootObjs);
	
	if(PyErr_Occurred()) PyErr_Print();
}

void setupMenu() {
	// http://qt-project.org/doc/qt-4.8/qmenubar.html#QMenuBar
	// I guess it's Mac specific to create the menu bar this way.
	
	mainMenuBar = new QMenuBar(0);
	QMenuBar* menu = mainMenuBar;
	
	QMenu* m;
	QAction* act;
	//m = menu->addMenu("Edit");
	
	m = menu->addMenu("Window");
	iterRootObjs(m);
	
	//act->
	//m->addAction();
	
	
	// TODO...
}
