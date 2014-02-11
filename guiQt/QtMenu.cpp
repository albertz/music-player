

#include "QtMenu.hpp"
#include "QtApp.hpp"
#include "PyThreading.hpp"
#include "PythonHelpers.h"
#include "PyUtils.h"
#include <QMenuBar>
#include <QPointer>

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

static QPointer<QMenu> controlMenu;
static QAction* control_song;
static QAction* control_playPause;
static QAction* control_nextSong;

void setupControlMenu(QMenu* m) {
	controlMenu = m;
	control_song = m->addAction("no song yet");
	control_playPause= m->addAction("Play", QtApp::instance(), SLOT(playPause()));
	control_nextSong = m->addAction("Next song", QtApp::instance(), SLOT(nextSong()));
	
#ifdef __APPLE__
	extern void qt_mac_set_dock_menu(QMenu *);
	qt_mac_set_dock_menu(m);
#endif
}

void updateControlMenu() {
	if(!controlMenu) return;
	
}

void setupMenu() {
	// http://qt-project.org/doc/qt-4.8/qmenubar.html#QMenuBar
	// I guess it's Mac specific to create the menu bar this way.
	
	mainMenuBar = new QMenuBar(0);
	QMenuBar* menu = mainMenuBar;
	
	QMenu* m;
	QAction* act;
	
	// http://stackoverflow.com/questions/21701694/how-to-create-edit-menu-in-qt-esp-macosx
	m = menu->addMenu("Edit");	
	m->addAction("Cut", QtApp::instance(), SLOT(edit_cut()), QKeySequence::Cut);
	m->addAction("Copy", QtApp::instance(), SLOT(edit_copy()), QKeySequence::Copy);
	m->addAction("Paste", QtApp::instance(), SLOT(edit_paste()), QKeySequence::Paste);
	m->addAction("Select all", QtApp::instance(), SLOT(edit_selectAll()), QKeySequence::SelectAll);
	
	m = menu->addMenu("Window");
	iterRootObjs(m);
	
	m = menu->addMenu("Control");
	setupControlMenu(m);
	
	//act->
	//m->addAction();
	
	
	// TODO...
}

