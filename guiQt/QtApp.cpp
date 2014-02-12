
#include "QtApp.hpp"
#include "QtMenu.hpp"
#include "PythonHelpers.h"
#include "PyUtils.h"
#include "PyThreading.hpp"
#include "PyQtGuiObject.hpp"
#include "QtBaseWidget.hpp"
#include <QAction>
#include <QTextCodec>
#include <sys/types.h>
#include <unistd.h>

// Dummy vars for QApplication.
// Note that the App construction is late at init. The Python code
// has already parsed all args and warned about unknown ones, etc.
// If we want to allow some Qt args, we should add some Python arg
// like "--qtargs" and pass those here.
static int dummy_argc = 1;
static char* dummy_argv[] = {(char*)"musicplayer", NULL};

static pid_t qtApp_pid;

QtApp::QtApp() : QApplication(dummy_argc, dummy_argv) {
	{
		QByteArray normalizedSignature = QMetaObject::normalizedSignature("genericExec(boost::function<void(void)>)");
		int methodIndex = this->metaObject()->indexOfSlot(normalizedSignature);
		assert(methodIndex >= 0);
		genericExec_method = this->metaObject()->method(methodIndex);
	}

#if QT_VERSION < 0x050000
	// This only exists in Qt4. Afaik, Qt5 uses utf8 by default.
	QTextCodec::setCodecForCStrings(QTextCodec::codecForName("utf8"));
#endif
	
	qtApp_pid = getpid();
	
	this->setOrganizationName("Albert Zeyer");
	this->setApplicationName("MusicPlayer");
	this->setQuitOnLastWindowClosed(false);
	
	connect(this, SIGNAL(aboutToQuit()), this, SLOT(handleApplicationQuit()));
}

bool QtApp::isFork() {
	return qtApp_pid != getpid();
}

void QtApp::handleApplicationQuit() {
	PyScopedGIL gil;
	
	printf("about to quit ...\n");
	
	PyObject* guiMod = getModule("gui"); // borrowed
	if(!guiMod) {
		printf("QtApp::handleApplicationQuit: gui module not found");
		return;
	}

	PyObject* ret = PyObject_CallMethod(guiMod, (char*)"handleApplicationQuit", NULL);
	if(!ret && PyErr_Occurred()) PyErr_Print();
	Py_XDECREF(ret);
}

void QtApp::openWindowViaMenu() {
	if(sender() == NULL) {
		printf("QtApp::openWindowViaMenu: no sender\n");
		return;
	}

	QAction* act = qobject_cast<QAction*>(sender());
	if(!act) {
		printf("QtApp::openWindowViaMenu: sender is not QAction\n");
		return;
	}
	if(act->objectName().isEmpty()) {
		printf("QtApp::openWindowViaMenu: sender name is empty\n");
		return;
	}
	
	openWindow(act->objectName().toStdString());
}

void QtApp::openMainWindow() {
	openWindow("Main");
}

void QtApp::openWindow(const std::string& name) {
	PyScopedGIL gil;

	PyObject* rootObj = handleModuleCommand("gui", "RootObjs.__getitem__", "(s)", name.c_str());
	if(!rootObj) return; // Python errs already handled in handleModuleCommand
	
	PyQtGuiObject* control = NULL;
	control = (PyQtGuiObject*) PyObject_GetAttrString(rootObj, "guiObj");
	if(!control) {
		if(PyErr_Occurred()) PyErr_Print();
		Py_DECREF(rootObj);
		return;		
	}
	
	if((PyObject*) control == Py_None) Py_CLEAR(control);
	if(control) {
		if(PyType_IsSubtype(Py_TYPE(control), &QtGuiObject_Type)) {
			QtBaseWidget* win = control->widget;
			if(win) {
				win->show();
				return;
			}
			// continue with existing control but create new window
		}
		else {
			printf("Qt open window: existing rootObj.guiObj is of wrong type\n");
			// reset and continue with new control creation
			Py_CLEAR(control);			
		}
	}
	
	if(!control) {
		control = (PyQtGuiObject*) PyObject_CallFunction((PyObject*) &QtGuiObject_Type, NULL);
		if(!control) {
			if(PyErr_Occurred()) PyErr_Print();
			Py_DECREF(rootObj);
			return;
		}

		assert(control->root == NULL);
		control->root = control;
		Py_XINCREF(control->root);		
		assert(control->subjectObject == NULL);
		control->subjectObject = PyObject_GetAttrString(rootObj, "obj");
		if(!control->subjectObject) {
			if(PyErr_Occurred()) PyErr_Print();			
			Py_DECREF(rootObj);
			Py_DECREF(control);
			return;
		}
	}
	
	if(PyObject_SetAttrString(rootObj, "guiObj", (PyObject*) control) < 0) {
		if(PyErr_Occurred()) PyErr_Print();
		Py_DECREF(rootObj);
		Py_DECREF(control);
		return;		
	}
	
	// check subjectObject
	{
		PyObject* subjectObject = PyObject_GetAttrString(rootObj, "obj");
		if(!subjectObject) {
			if(PyErr_Occurred()) PyErr_Print();
			// continue, maybe it doesn't matter			
		}
		else {
			if(subjectObject != control->subjectObject) {
				printf("Qt open window: got new subject object\n");
				// strange, but just overtake and continue
				Py_CLEAR(control->subjectObject);
				control->subjectObject = subjectObject;
				subjectObject = NULL;
			}
		}
		Py_XDECREF(subjectObject);
	}
	
	QtBaseWidget* win = new QtBaseWidget(control);
	control->widget = win;
	win->setAttribute(Qt::WA_DeleteOnClose);	
	
	// set title
	{
		PyObject* title = PyObject_GetAttrString(rootObj, "title");
		std::string titleStr;
		if(!title || !pyStr(title, titleStr)) {
			if(PyErr_Occurred()) PyErr_Print();			
			win->setWindowTitle(QString::fromStdString(name));
		}
		else {			
			win->setWindowTitle(QString::fromStdString(titleStr));
		}
		Py_XDECREF(title);
	}
	
	Vec size = control->setupChilds();
	win->setMinimumSize(size.x, size.y);

	// ...
	
	win->show();
	
	Py_DECREF(rootObj);
	Py_DECREF(control);
}

void QtApp::minimizeWindow() {
	QWidget* win = qApp->activeWindow();
	if(win) win->showMinimized();
}

void QtApp::closeWindow() {
	QWidget* win = qApp->activeWindow();
	if(win) win->close();
}

void QtApp::edit_cut() {
	QWidget* w = QApplication::focusWidget();
	//...
}

void QtApp::edit_copy() {
	
}

void QtApp::edit_paste() {
	
}

void QtApp::edit_selectAll() {
	
}

void QtApp::handlePlayerUpdate() {
	updateControlMenu();
}

void QtApp::playPause() {
	handleModuleCommand_noReturn("State", "state.playPause", NULL);
}

void QtApp::nextSong() {
	handleModuleCommand_noReturn("State", "state.nextSong", NULL);
}

void QtApp::debug_resetPlayer() {
	handleModuleCommand_noReturn("State", "state.player.resetPlaying", NULL);
}
