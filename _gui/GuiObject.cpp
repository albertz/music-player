#include "GuiObject.hpp"

int GuiObject::init(PyObject* args, PyObject* kwds) {
	return 0;
}

PyObject* GuiObject::getattr(const char* key) {
	PyErr_Format(PyExc_AttributeError, "GuiObject has no attribute '%.400s'", key);
	return NULL;
	
returnNone:
	Py_INCREF(Py_None);
	return Py_None;
}

int GuiObject::setattr(const char* key, PyObject* value) {
	PyObject* s = PyString_FromString(key);
	if(!s) return -1;
	// While we have no own __dict__, this will fail. But that is what we want.
	int ret = PyObject_GenericSetAttr((PyObject*) this, s, value);
	Py_XDECREF(s);
	return ret;
}
