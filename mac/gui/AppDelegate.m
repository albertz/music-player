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

PyObject* getPlayerState() {
	PyObject* mod = getModule("State"); // borrowed
	if(!mod) return NULL;
	return PyObject_GetAttrString(mod, "state");
}

PyObject* attrChain(PyObject* base, const char* name) {
	PyObject* res = NULL;
	Py_INCREF(base);
	
	while(true) {
		char* dot = strchr(name, '.');
		if(!dot) break;
		
		PyObject* attrName = PyString_FromStringAndSize(name, dot - name);
		if(!attrName)
			goto final;
			
		PyObject* nextObj = PyObject_GetAttr(base, attrName);
		Py_DECREF(attrName);
		if(!nextObj)
			goto final;

		Py_DECREF(base);
		base = nextObj;
		name = dot + 1;
	}
	
	res = PyObject_GetAttrString(base, name);
	
final:
	Py_XDECREF(base);
	return res;
}

void handlePlayerStateCommand(const char* cmd) {
	PyGILState_STATE gstate = PyGILState_Ensure();
	
	PyObject* state = getPlayerState();
	PyObject* func = NULL;
	PyObject* ret = NULL;

	if(!state) {
		printf("Warning: Did not get State.state.\n");
		goto final;
	}
	func = attrChain(state, cmd);
	if(!func) {
		printf("Warning: Did not get State.state.%s.\n", cmd);
		goto final;
	}
	ret = PyObject_CallFunction(func, NULL);
	
final:
	if(PyErr_Occurred())
		PyErr_Print();
	
	Py_XDECREF(state);
	Py_XDECREF(func);
	Py_XDECREF(ret);
	PyGILState_Release(gstate);
}

@implementation AppDelegate

NSWindow* mainWindow;

- (void)setupMainWindow
{
	
}

- (void)setupSearchWindow
{
	
}

- (void)setupSongEditWindow
{
	
}

MSMenu* dockMenu;

- (void)updateControlMenu
{
//	if not AppKit.NSApp: return
//	menu = getattr(AppKit.NSApp.delegate(), "dockMenu", None)
//	if not menu: return
//	from State import state
//	if not state: return
//	songEntry = menu.itemAtIndex_(0)
//	playPauseEntry = menu.itemAtIndex_(1)
//	songEntry.setTitle_(convertToUnicode(state.curSong.userString))
//	if state.player.playing:
//		playPauseEntry.setTitle_("Pause")
//	else:
//		playPauseEntry.setTitle_("Play")		

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
	[self setupSearchWindow];
}

- (void)openSongEditWindow:(id)sender
{
	[self setupSongEditWindow];
}

- (void)about:(id)sender
{
	PyGILState_STATE gstate = PyGILState_Ensure();
	
	PyObject* mod = getModule("gui"); // borrowed
	PyObject* callback = NULL;
	PyObject* ret = NULL;
	if(!mod) {
		printf("Warning: Did not find gui module.\n");
		goto final;
	}
	callback = PyObject_GetAttrString(mod, "about");
	if(!callback) {
		printf("Warning: gui.about not found.\n");
		goto final;
	}
	ret = PyObject_CallFunction(callback, NULL);
	
final:
	if(PyErr_Occurred())
		PyErr_Print();
	
	Py_XDECREF(ret);
	Py_XDECREF(callback);
	PyGILState_Release(gstate);
}

- (void)playPause:(id)sender
{
	handlePlayerStateCommand("playPause");
}

- (void)nextSong:(id)sender
{
	handlePlayerStateCommand("nextSong");
}

- (void)resetPlayer:(id)sender
{
	handlePlayerStateCommand("player.resetPlaying");
}

- (void)dealloc
{
	printf("My app delegate dealloc\n");
}

@end
