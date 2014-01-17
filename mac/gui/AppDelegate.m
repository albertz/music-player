//
//  AppDelegate.m
//  MusicPlayer
//
//  Created by Albert Zeyer on 17.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include <Python.h>
#include <dlfcn.h>
#import "AppDelegate.h"


static void handleFatalError(const char* msg) {
	typedef void Handler(const char* msg);
	Handler* handler = (Handler*) dlsym(RTLD_DEFAULT, "handleFatalError");
	if(handler)
		handler(msg);
	else
		printf("Error^2: Error handler not found. This is probably not executed within the orig exec.\n");
	exit(1);
}

PyObject* getModule(const char* name) {
	PyObject *modules = PyImport_GetModuleDict(); // borrowed ref
	if(!modules) return NULL;
	return PyDict_GetItemString(modules, name); // borrowed ref
}

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)aNotification
{
	printf("My app delegate: finish launching\n");
	
	const char* fatalErrorMsg = NULL;
	PyObject* mod = getModule("guiCocoa"); // borrowed
	PyObject* callback = NULL;
	PyObject* ret = NULL;
	if(!mod) {
		fatalErrorMsg = "Startup error. Did not loaded guiCocoa correctly.";
		goto final;
	}
	callback = PyObject_GetAttrString(mod, "setupAfterAppFinishedLaunching");
	if(!callback) {
		fatalErrorMsg = "Startup error. setupAfterAppFinishedLaunching not found.";
		goto final;
	}
	ret = PyObject_CallFunction(callback, NULL);
	
final:
	if(PyErr_Occurred()) {
		PyErr_Print();
		if(!fatalErrorMsg)
			fatalErrorMsg = "Startup error. Unknown Python exception occured.";
	}
	
	if(fatalErrorMsg)
		handleFatalError(fatalErrorMsg);
	
	Py_XDECREF(ret);
	Py_XDECREF(callback);
}

- (NSApplicationTerminateReply)applicationShouldTerminate:(NSNotification *)aNotification
{
	printf("My app delegate: should terminate\n");

	Py_BEGIN_ALLOW_THREADS
		
	PyObject* mod = getModule("guiCocoa"); // borrowed
	PyObject* callback = NULL;
	PyObject* ret = NULL;
	if(!mod) {
		printf("Warning: Did not find guiCocoa.\n");
		goto final;
	}
	callback = PyObject_GetAttrString(mod, "handleApplicationQuit");
	if(!callback) {
		printf("Warning: handleApplicationQuit not found.\n");
		goto final;
	}
	ret = PyObject_CallFunction(callback, NULL);
	
final:
	if(PyErr_Occurred())
		PyErr_Print();
	
	Py_XDECREF(ret);
	Py_XDECREF(callback);
	Py_END_ALLOW_THREADS
	
	return NSTerminateNow;
}

- (void)dealloc
{
	printf("My app delegate dealloc\n");
}

@end
