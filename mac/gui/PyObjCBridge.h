#ifndef MP_PyObjCBridge
#define MP_PyObjCBridge

#include <Python.h>
#import <Cocoa/Cocoa.h>

id PyObjCObj_GetNativeObj(PyObject* obj);

#endif

