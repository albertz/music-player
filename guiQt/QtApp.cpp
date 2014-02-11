
#include "QtApp.hpp"
#include "PythonHelpers.h"
#include "PyThreading.hpp"
#include <QAction>

// Dummy vars for QApplication.
// Note that the App construction is late at init. The Python code
// has already parsed all args and warned about unknown ones, etc.
// If we want to allow some Qt args, we should add some Python arg
// like "--qtargs" and pass those here.
static int dummy_argc = 1;
static char* dummy_argv[] = {(char*)"musicplayer", NULL};

QtApp::QtApp() : QApplication(dummy_argc, dummy_argv) {
	{
		QByteArray normalizedSignature = QMetaObject::normalizedSignature("genericExec(boost::function<void(void)>)");
		int methodIndex = this->metaObject()->indexOfSlot(normalizedSignature);
		assert(methodIndex >= 0);
		genericExec_method = this->metaObject()->method(methodIndex);
	}

	this->setOrganizationName("Albert Zeyer");
	this->setApplicationName("MusicPlayer");
	
	connect(this, SIGNAL(aboutToQuit()), this, SLOT(handleApplicationQuit()));
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

void QtApp::playPause() {
	
}

void QtApp::nextSong() {
	
}
