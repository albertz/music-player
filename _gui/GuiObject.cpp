#include "GuiObject.hpp"

int GuiObject::init(PyObject* args, PyObject* kwds) {
	DefaultSpace = Vec(8,8);
	OuterSpace = Vec(8,8);
	return 0;
}

static PyObject* returnObj(PyObject* obj) {
	if(!obj) obj = Py_None;
	Py_INCREF(obj);
	return obj;
}

#define _ReturnAttr(attr) { if(strcmp(key, #attr) == 0) return returnObj(attr); }

static PyObject* returnVec(const Vec& v) {
	PyObject* t = PyTuple_New(2);
	if(!t) return NULL;
	PyTuple_SET_ITEM(t, 0, PyInt_FromLong(v.x));
	PyTuple_SET_ITEM(t, 1, PyInt_FromLong(v.y));
	return t;
}

#define _ReturnAttrVec(attr) { if(strcmp(key, #attr) == 0) return returnVec(attr); }

static PyObject* returnAutoresize(const Autoresize& v) {
	PyObject* t = PyTuple_New(4);
	if(!t) return NULL;
	PyTuple_SET_ITEM(t, 0, PyBool_FromLong(v.x));
	PyTuple_SET_ITEM(t, 1, PyBool_FromLong(v.y));
	PyTuple_SET_ITEM(t, 2, PyBool_FromLong(v.w));
	PyTuple_SET_ITEM(t, 3, PyBool_FromLong(v.h));
	return t;
}

PyObject* GuiObject::getattr(const char* key) {
	_ReturnAttr(root);
	_ReturnAttr(parent);
	_ReturnAttr(attr);
	_ReturnAttr(nativeGuiObject);
	_ReturnAttr(subjectObject);
	_ReturnAttrVec(pos);
	_ReturnAttrVec(size);
	_ReturnAttrVec(DefaultSpace);
	_ReturnAttrVec(OuterSpace);
		
	if(strcmp(key, "autoresize") == 0)
		return returnAutoresize(autoresize);

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
