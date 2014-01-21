#ifndef MP_PyObjCBridge
#define MP_PyObjCBridge

#include <Python.h>
#import <Cocoa/Cocoa.h>


#ifdef __cplusplus
extern "C" {
#endif

id PyObjCObj_GetNativeObj(PyObject* obj);
PyObject* PyObjCObj_NewNative(id obj);

#ifdef __cplusplus
}
#endif

#endif

