

#include "QtMenu.hpp"
#include "QtApp.hpp"
#include <QMenuBar>

QMenuBar* mainMenuBar = NULL;

void setupMenu() {
	// http://qt-project.org/doc/qt-4.8/qmenubar.html#QMenuBar
	// I guess it's Mac specific to create the menu bar this way.
	
	mainMenuBar = new QMenuBar(0);
	QMenuBar* menu = mainMenuBar;
	
	QMenu* m;
	QAction* act;
	//m = menu->addMenu("Edit");
	
	m = menu->addMenu("Window");
	act = m->addAction("Main window", QtApp::instance(), SLOT(openWindowViaMenu()));
	
	//act->
	//m->addAction();
	
	
	// TODO...
}
