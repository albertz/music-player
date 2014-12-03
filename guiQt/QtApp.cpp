
#include "QtApp.hpp"
#include "QtMenu.hpp"
#include "PythonHelpers.h"
#include "PyUtils.h"
#include "PyThreading.hpp"
#include "PyQtGuiObject.hpp"
#include "QtBaseWidget.hpp"
#include <QAction>
#include <QTextCodec>
#include <QThread>
#include <QApplication>
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

// defined in app.
extern std::string getResourcePath();

Q_DECLARE_METATYPE(QtFunc);

void QtApp::prepareInit() {
	printf("Qt Version: %s\n", qVersion());

	// Needed so that it finds libqcocoa.dylib on MacOSX.
	QCoreApplication::setLibraryPaths(QStringList() << QString::fromStdString(getResourcePath()));

#if QT_VERSION < 0x050000
	// This only exists in Qt4. Afaik, Qt5 uses utf8 by default.
	QTextCodec::setCodecForCStrings(QTextCodec::codecForName("utf8"));
#endif

#ifdef Q_OS_MACX
	// fix OSX 10.9 font
	// http://successfulsoftware.net/2013/10/23/fixing-qt-4-for-mac-os-x-10-9-mavericks/
	// https://bugreports.qt-project.org/browse/QTBUG-32789
	QFont::insertSubstitution(".Lucida Grande UI", "Lucida Grande");
	// fix OSX 10.10 font
	// https://bugreports.qt-project.org/browse/QTBUG-40833
	QFont::insertSubstitution(".Helvetica Neue DeskInterface", "Helvetica Neue");
#endif

	// This forces that the type is registered in Qt.
	qMetaTypeId<QtFunc>();
}

QtApp::QtApp() : QApplication(dummy_argc, dummy_argv) {
	{
		QByteArray normalizedSignature = QMetaObject::normalizedSignature("genericExec(QtFunc)");
		int methodIndex = this->metaObject()->indexOfSlot(normalizedSignature);
		assert(methodIndex >= 0);
		genericExec_method = this->metaObject()->method(methodIndex);
	}

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

bool QtApp::openMainWindow() {
	return openWindow("Main");
}

bool QtApp::openWindow(const std::string& name) {
	assert(QThread::currentThread() == qApp->thread());
	
	PyScopedGIL gil;

	PyObject* rootObj = handleModuleCommand("gui", "RootObjs.__getitem__", "(s)", name.c_str());
	if(!rootObj) return false; // Python errs already handled in handleModuleCommand
	
	PyQtGuiObject* control = NULL;
	control = (PyQtGuiObject*) PyObject_GetAttrString(rootObj, "guiObj");
	if(!control) {
		if(PyErr_Occurred()) PyErr_Print();
		Py_DECREF(rootObj);
		return false;		
	}
	
	if((PyObject*) control == Py_None) Py_CLEAR(control);
	if(control) {
		if(PyType_IsSubtype(Py_TYPE(control), &QtGuiObject_Type)) {
			QtBaseWidget::ScopedRef win(control->widget);
			if(win) {
				win->show();
				return true;
			}
			// continue with existing control but create new window
		}
		else {
			printf("Qt open window: existing rootObj.guiObj is of wrong type\n");
			// reset and continue with new control creation
			Py_CLEAR(control);			
		}
	}
	
	// We have no control object yet, so create one.
	if(!control) {
		PyObject* subjectObject = PyObject_GetAttrString(rootObj, "obj");
		if(!subjectObject) {
			if(PyErr_Occurred()) PyErr_Print();
			Py_DECREF(rootObj);
			return false;
		}

		control = guiQt_createControlObject(subjectObject, /* we are root */ NULL);
		if(!control) {
			if(PyErr_Occurred()) PyErr_Print();
			Py_DECREF(rootObj);
			Py_DECREF(subjectObject);
			return false;
		}
		Py_CLEAR(subjectObject);
	}
	
	if(PyObject_SetAttrString(rootObj, "guiObj", (PyObject*) control) < 0) {
		if(PyErr_Occurred()) PyErr_Print();
		Py_DECREF(rootObj);
		Py_DECREF(control);
		return false;		
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

	// TODO?...
	// XXX: set control->widget = win?

	win->show();
	//control->layout(); // XXX ?
	
	win->activateWindow();
	win->raise();
	
	Py_DECREF(rootObj);
	Py_DECREF(control);
	return true;
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
	// TODO...
}

void QtApp::edit_copy() {
	// TODO...
}

void QtApp::edit_paste() {
	// TODO...
}

void QtApp::edit_selectAll() {
	// TODO...
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
