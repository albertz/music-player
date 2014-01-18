//
//  AppDelegate.m
//  MusicPlayer
//
//  Created by Albert Zeyer on 17.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include <Python.h>
#include <dlfcn.h>
#import "PyObjCBridge.h"
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

PyObject* _handleModuleCommand(const char* modName, const char* cmd, const char* paramFormat, va_list va) {
	PyGILState_STATE gstate = PyGILState_Ensure();
	
	PyObject* mod = getModule(modName); // borrowed
	PyObject* func = NULL;
	PyObject* args = NULL;
	PyObject* ret = NULL;

	if(!mod) {
		printf("Warning: Did not found module %s.\n", modName);
		goto final;
	}	
	func = attrChain(mod, cmd);
	if(!func) {
		printf("Warning: Did not get %s.%s.\n", modName, cmd);
		goto final;
	}

    if (paramFormat && *paramFormat) {
        args = Py_VaBuildValue(paramFormat, va);
		if(!args) goto final;

		if (!PyTuple_Check(args)) {
			PyObject* newArgs = PyTuple_New(1);
			if(!newArgs) goto final;
			PyTuple_SET_ITEM(newArgs, 0, args);
			args = newArgs;
		}
    }
    else
        args = PyTuple_New(0);
	
	ret = PyObject_Call(func, args, NULL);
	
final:
	if(PyErr_Occurred())
		PyErr_Print();
	
	Py_XDECREF(func);
	Py_XDECREF(args);
	PyGILState_Release(gstate);
	
	return ret;
}

PyObject* handleModuleCommand(const char* modName, const char* cmd, const char* paramFormat, ...) {
	va_list va;
	va_start(va, paramFormat);
	PyObject* ret = _handleModuleCommand(modName, cmd, paramFormat, va);
	va_end(va);
	return ret;
}

void handleModuleCommand_noReturn(const char* modName, const char* cmd, const char* paramFormat, ...) {
	PyGILState_STATE gstate = PyGILState_Ensure();
	va_list va;
	va_start(va, paramFormat);
	PyObject* ret = _handleModuleCommand(modName, cmd, paramFormat, va);
	va_end(va);
	Py_XDECREF(ret);
	PyGILState_Release(gstate);
}

NSString* _convertToUnicode(PyObject* obj) {
	NSString* resStr = nil;
	PyObject* res = handleModuleCommand("utils", "convertToUnicode", "(o)", obj);
	if(!res) resStr = @"<convertToUnicode error>";
	else if(PyString_Check(res)) {
		const char* s = PyString_AS_STRING(res);
		if(!s) resStr = @"<NULL>";
		else resStr = [NSString stringWithUTF8String:s];
	}
	else if(PyUnicode_Check(res)) {
		PyObject* utf8Str = PyUnicode_AsUTF8String(res);
		if(!utf8Str) resStr = @"<conv-utf8 failed>";
		const char* s = PyString_Check(utf8Str) ? PyString_AS_STRING(utf8Str) : NULL;
		if(!s) resStr = @"<conv-utf8 error>";
		else resStr = [NSString stringWithUTF8String:s];
	}
	else resStr = @"<convertToUnicode invalid>";
	return resStr;
}

NSWindow* getWindow(const char* name) {
	NSWindow* res = NULL;

	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject* w = handleModuleCommand("guiCocoa", "getWindow", "(s)", name);
	if(!w) goto final;
	res = PyObjCObj_GetNativeObj(w);
	
final:
	Py_XDECREF(w);
	PyGILState_Release(gstate);
	
	return res;
}


@implementation AppDelegate

- (void)setupMainWindow
{
	handleModuleCommand_noReturn("guiCocoa", "setupMainWindow", NULL);
}

- (void)setupSearchWindow
{
	handleModuleCommand_noReturn("guiCocoa", "setupSearchWindow", NULL);
}

- (void)setupSongEditWindow
{
	handleModuleCommand_noReturn("guiCocoa", "setupSongEditWindow", NULL);
}

NSMenu* dockMenu;

- (void)setDockMenu:(NSMenu*)m
{
	dockMenu = m;
}

- (void)updateControlMenu
{
	if(!dockMenu) return;

	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject* mod = getModule("State"); // borrowed
	PyObject* state = NULL;
	PyObject* songTitle = NULL;
	PyObject* playingState = NULL;
	
	if(!mod) goto final;
	state = attrChain(mod, "state");
	if(!state || PyObject_IsTrue(state) <= 0) goto final;
	
	songTitle = attrChain(mod, "state.curSong.userString");
	if(!songTitle) goto final;
	playingState = attrChain(mod, "state.player.playing");
	if(!playingState) goto final;
		
	{
		NSMenuItem* songEntry = [dockMenu itemAtIndex:0];
		NSMenuItem* playPauseEntry = [dockMenu itemAtIndex:1];

		[songEntry setTitle:_convertToUnicode(songTitle)];
		[playPauseEntry setTitle:((PyObject_IsTrue(playingState) > 0) ? @"Pause" : @"Play")];
	}
	
final:
	if(PyErr_Occurred())
		PyErr_Print();

	Py_XDECREF(state);
	Py_XDECREF(songTitle);
	Py_XDECREF(playingState);
	PyGILState_Release(gstate);
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
	handleModuleCommand_noReturn("guiCocoa", "handleApplicationQuit", NULL);
	return NSTerminateNow;
}

- (BOOL)applicationOpenUntitledFile:(NSApplication *)sender
{
	if(!getWindow("mainWindow"))
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
	handleModuleCommand_noReturn("State", "state.playPause", NULL);
}

- (void)nextSong:(id)sender
{
	handleModuleCommand_noReturn("State", "state.nextSong", NULL);
}

- (void)resetPlayer:(id)sender
{
	handleModuleCommand_noReturn("State", "state.player.resetPlaying", NULL);
}

- (void)dealloc
{
	printf("My app delegate dealloc\n");
}

@end
