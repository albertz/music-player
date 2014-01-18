//
//  PythonHelpers.h
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef MusicPlayer_PythonHelpers_h
#define MusicPlayer_PythonHelpers_h

#include <Python.h>
#import <Foundation/Foundation.h>

inline
PyObject* getModule(const char* name) {
	PyObject *modules = PyImport_GetModuleDict(); // borrowed ref
	if(!modules) return NULL;
	return PyDict_GetItemString(modules, name); // borrowed ref
}

inline
PyObject* getPlayerState() {
	PyObject* mod = getModule("State"); // borrowed
	if(!mod) return NULL;
	return PyObject_GetAttrString(mod, "state");
}

inline
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

inline
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

inline
PyObject* handleModuleCommand(const char* modName, const char* cmd, const char* paramFormat, ...) {
	va_list va;
	va_start(va, paramFormat);
	PyObject* ret = _handleModuleCommand(modName, cmd, paramFormat, va);
	va_end(va);
	return ret;
}

inline
void handleModuleCommand_noReturn(const char* modName, const char* cmd, const char* paramFormat, ...) {
	PyGILState_STATE gstate = PyGILState_Ensure();
	va_list va;
	va_start(va, paramFormat);
	PyObject* ret = _handleModuleCommand(modName, cmd, paramFormat, va);
	va_end(va);
	Py_XDECREF(ret);
	PyGILState_Release(gstate);
}

inline
NSString* convertToStr(PyObject* obj) {
	NSString* resStr = nil;
	PyObject* res = handleModuleCommand("utils", "convertToUnicode", "(O)", obj);
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


#endif
