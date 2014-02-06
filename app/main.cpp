//
//  main.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 06.02.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include <Python.h>
#include <stdio.h>
#include <signal.h>

#include "sysutils.hpp"


#ifndef __APPLE__
#warning "No implementation of AmIBeingDebugged()"
bool AmIBeingDebugged() { return false; }
#endif



bool logEnabled = false;
#ifdef __APPLE__
std::string logFilename = "~/Library/Logs/com.albertzeyer.MusicPlayer.log";
#else
std::string logFilename = "~/.com.albertzeyer.MusicPlayer/musicplayer.log";
#endif


bool forkExecProc = false;

static void addPyPath() {
	std::string path = getResourcePath() + "/Python:" + Py_GetPath();	
	PySys_SetPath((char*)path.c_str());
	if(!forkExecProc)
		printf("Python path: %s\n", path.c_str());
}

static int sys_argc;
static char** sys_argv;

static bool haveArg(const char* arg) {
	for(int i = 1; i < sys_argc; ++i)
		if(strcmp(sys_argv[i], arg) == 0) {
			return true;
		}
	return false;
}

static bool checkStartupSuccess() {
	PyObject* mods = PyImport_GetModuleDict();
	if(!mods) return false;
	PyObject* m = PyDict_GetItemString(mods, "main");
	if(!m) return false;

	PyObject* successObj = PyObject_GetAttrString(m, "successStartup");
	bool success = false;
	if(successObj)
		success = PyObject_IsTrue(successObj);
	
	Py_XDECREF(successObj);
	mods = NULL; // borrowed
	m = NULL; // borrowed
	
	return success;
}



void signal_handler(int sig) {
	handleFatalError("There was a fatal error.");
}

void install_signal_handler() {
	signal(SIGABRT, signal_handler);
	signal(SIGBUS, signal_handler);
	signal(SIGSEGV, signal_handler);
	signal(SIGFPE, signal_handler);
	signal(SIGILL, signal_handler);
}

#ifdef __APPLE__
const char* StartupStr = "Hello from MusicPlayer on MacOSX.\n";
#else
const char* StartupStr = "Hello from MusicPlayer.\n";
#endif


int main(int argc, char *argv[])
{
	sys_argc = argc;
	sys_argv = argv;
	
	forkExecProc = haveArg("--forkExecProc");
	bool shell = haveArg("--shell");
	bool pyShell = haveArg("--pyshell");
	bool pyExec = haveArg("--pyexec");
	bool noLog = haveArg("--nolog");
	bool help = haveArg("--help") || haveArg("-h");
	bool beingDebugged = AmIBeingDebugged();
	
	const char* logDisabledReason = NULL;
	if(pyShell || pyExec || shell || forkExecProc || help) {} // be quiet
	else if(beingDebugged) {
		logDisabledReason = "debugger detected, not redirecting stdout/stderr";
	}
	else if(noLog) {
		logDisabledReason = "not redirecting stdout/stderr";
	}
	else {
		// current workaround to log stdout/stderr. see http://stackoverflow.com/questions/13104588/how-to-get-stdout-into-console-app
		logEnabled = true;
		printf("MusicPlayer: stdout/stderr goes to %s now\n", logFilename.c_str());
		fflush(stdout);
		int newFd = open(logFilename.c_str(), O_WRONLY|O_APPEND|O_CREAT);
		dup2(newFd, fileno(stdout));
		dup2(newFd, fileno(stderr));
		close(newFd);
		//freopen(logFilename.c_str(), "a", stdout);
		//freopen(logFilename.c_str(), "a", stderr);
		stderr = stdout; // well, hack, ... I don't like two seperate buffers. just messes up the output
	}

	if(!forkExecProc) {
		printf("%s", StartupStr);
		install_signal_handler();
	}
	
	if(help) {
		printf(
			   "Help: Available options:\n"
			   "  --nolog		: don't redirect stdout/stderr to log. also implied when run in debugger\n"
			   );
	}

	if(!logEnabled && logDisabledReason)
		printf("%s\n", logDisabledReason);

	std::string mainPyFilename = getResourcePath() + "/Python/main.py";
	Py_SetProgramName(argv[0]);
	if(!forkExecProc)
		printf("Python version: %s, prefix: %s, main: %s\n", Py_GetVersion(), Py_GetPrefix(), mainPyFilename.c_str());
	
	Py_Initialize();
	PyEval_InitThreads();
	addPyPath();

	if(logEnabled) {
		PySys_SetObject("stdout", PyFile_FromFile(stdout, "<stdout>", "w", fclose));
		PySys_SetObject("stderr", PySys_GetObject("stdout"));
	}

	// Preload imp and thread. I hope to fix this bug: https://github.com/albertz/music-player/issues/8 , there was a crash in initthread which itself has called initimp
	PyObject* m = NULL;
	m = PyImport_ImportModule("imp");
	Py_XDECREF(m);
	m = PyImport_ImportModule("thread");
	Py_XDECREF(m);
	
	PySys_SetArgvEx(argc, argv, 0);
			
	FILE* fp = fopen((char*)mainPyFilename.c_str(), "r");
	assert(fp);
	PyRun_SimpleFile(fp, "main.py");
	
	if(!forkExecProc && !help && !pyShell && !pyExec && !shell) {
		bool successStartup = checkStartupSuccess();
		if(!successStartup) {
			printf("Error at startup.\n");
			handleFatalError("There was an error at startup.");
		}
	}
	
	return 0;
}
