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

NSWindow* mainWindow;

- (void)setupMainWindow
{
	
}

- (void)applicationDidFinishLaunching:(NSNotification *)aNotification
{
	printf("My app delegate: finish launching\n");
	
	PyGILState_STATE gstate = PyGILState_Ensure();
	
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
	PyGILState_Release(gstate);
}

- (NSApplicationTerminateReply)applicationShouldTerminate:(NSNotification *)aNotification
{
	printf("My app delegate: should terminate\n");

	PyGILState_STATE gstate = PyGILState_Ensure();
		
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
	PyGILState_Release(gstate);
	
	return NSTerminateNow;
}

- (BOOL)applicationOpenUntitledFile:(NSApplication *)sender
{
	if(!mainWindow)
		[self setupMainWindow];
	else
		[NSApp activateIgnoringOtherApps:YES];
	return YES;
}

// for NSUserNotificationCenterDelegate, >= MacOSX 10.8
- (BOOL)userNotificationCenter:(id)center shouldPresentNotification:(id)notification
{
	return YES;
}

- (void)openMainWindow:(id)sender
{
	[self setupMainWindow];
}

- (void)openSearchWindow:(id)sender
{
	// ...
}

//	def openSearchWindow_(self, app):
//		setupSearchWindow()
//	
//	def openSongEditWindow_(self, app):
//		setupSongEditWindow()
//
//	def about_(self, app):
//		import gui
//		gui.about()
//
//	def playPause_(self, app):
//		from State import state
//		state.playPause()
//	
//	def nextSong_(self, app):
//		from State import state
//		state.nextSong()
//
//	def resetPlayer_(self, app):
//		from State import state
//		state.player.resetPlaying()



- (void)dealloc
{
	printf("My app delegate dealloc\n");
}

@end
