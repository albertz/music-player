
#include <Python.h>
#include "pyobjc.h"
#import "PyObjCBridge.h"

id PyObjCObj_GetNativeObj(PyObject* obj) {
	if(!obj) return nil;
	if(!PyObjCObject_Check(obj)) return nil;
	return PyObjCObject_GetObject(obj);
}

PyObject* PyObjCObj_NewNative(id obj) {
	return PyObjCObject_New(obj, PyObjCObject_kDEFAULT, YES);
}

PyObject* PyObjCObj_IdToPy(id obj) {
	return PyObjC_IdToPython(obj);
}
