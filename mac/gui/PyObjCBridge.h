#ifndef MP_PyObjCBridge
#define MP_PyObjCBridge

#import <Cocoa/Cocoa.h>

struct PyObject;
id PyObjCObj_GetNativeObj(PyObject* obj);

#endif

