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

PyObject* Vec::asPyObject() const {
	PyObject* t = PyTuple_New(2);
	if(!t) return NULL;
	PyTuple_SET_ITEM(t, 0, PyInt_FromLong(x));
	PyTuple_SET_ITEM(t, 1, PyInt_FromLong(y));
	return t;
}

PyObject* Autoresize::asPyObject() const {
	PyObject* t = PyTuple_New(4);
	if(!t) return NULL;
	PyTuple_SET_ITEM(t, 0, PyBool_FromLong(x));
	PyTuple_SET_ITEM(t, 1, PyBool_FromLong(y));
	PyTuple_SET_ITEM(t, 2, PyBool_FromLong(w));
	PyTuple_SET_ITEM(t, 3, PyBool_FromLong(h));
	return t;
}

#define _ReturnAttrVec(attr) { if(strcmp(key, #attr) == 0) return attr.asPyObject(); }

#define _ReturnCustomAttr(attr) { \
	if(strcmp(key, #attr) == 0) { \
		if(get_ ## attr == 0) { \
			PyErr_Format(PyExc_AttributeError, "GuiObject attribute '%.400s' must be specified in subclass", key); \
			return NULL; \
		} \
		return (* get_ ## attr)(this).asPyObject(); \
	} }

PyObject* GuiObject::getattr(const char* key) {
	_ReturnAttr(root);
	_ReturnAttr(parent);
	_ReturnAttr(attr);
	_ReturnAttr(nativeGuiObject);
	_ReturnAttr(subjectObject);
	_ReturnAttrVec(DefaultSpace);
	_ReturnAttrVec(OuterSpace);
	
	_ReturnCustomAttr(pos);
	_ReturnCustomAttr(size);
	_ReturnCustomAttr(innerSize);
	_ReturnCustomAttr(autoresize);
	
	if(strcmp(key, "addChild") == 0) {
		PyErr_Format(PyExc_AttributeError, "GuiObject attribute '%.400s' must be specified in subclass", key);
		return NULL;
	}
	
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
