
#include "QtApp.hpp"

// Dummy vars for QApplication.
// Note that the App construction is late at init. The Python code
// has already parsed all args and warned about unknown ones, etc.
// If we want to allow some Qt args, we should add some Python arg
// like "--qtargs" and pass those here.
static int dummy_argc = 1;
static char* dummy_argv[] = {(char*)"musicplayer", NULL};

QtApp::QtApp() : QApplication(dummy_argc, dummy_argv) {
	this->setOrganizationName("Albert Zeyer");
	this->setApplicationName("MusicPlayer");	
}
