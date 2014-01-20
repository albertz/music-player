
#include "GuiObject.hpp"
#include "PythonHelpers.h"


int GuiObject::init(PyObject* args, PyObject* kwds) {
	// If the GuiObject type has no base set,
	// grab _GuiObject from the gui module and set it as the base.
	PyTypeObject* const selfType = &GuiObject_Type;
	if(selfType->tp_base == NULL || selfType->tp_base == &PyBaseObject_Type) {
		uninitTypeObject(selfType);

		PyObject* base = modAttrChain("gui", "_GuiObject");
		if(!base || PyErr_Occurred()) {
			if(PyErr_Occurred())
				PyErr_Print();
			Py_FatalError("Did not found gui._GuiObject.");
		}
		if(!PyClass_Check(base))
			Py_FatalError("gui._GuiObject is not a class.");
		selfType->tp_bases = PyTuple_Pack(1, base);
		Py_DECREF(base);
		
		if(PyType_Ready(selfType) < 0)
			Py_FatalError("Was not able to reinit type GuiObject.");
	}
	
	DefaultSpace = Vec(8,8);
	OuterSpace = Vec(8,8);
	return 0;
}


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

bool Vec::initFromPyObject(PyObject* obj) {
	if(!PyTuple_Check(obj)) {
		PyErr_Format(PyExc_ValueError, "Vec: We expect a tuple");
		return false;
	}
	if(PyTuple_GET_SIZE(obj) != 2) {
		PyErr_Format(PyExc_ValueError, "Vec: We expect a tuple with 2 elements");
		return false;
	}
	x = (int)PyInt_AsLong(PyTuple_GET_ITEM(obj, 0));
	y = (int)PyInt_AsLong(PyTuple_GET_ITEM(obj, 1));
	if(PyErr_Occurred())
		return false;
	return true;
}

bool Autoresize::initFromPyObject(PyObject* obj) {
	if(!PyTuple_Check(obj)) {
		PyErr_Format(PyExc_ValueError, "Autoresize: We expect a tuple");
		return false;
	}
	if(PyTuple_GET_SIZE(obj) != 4) {
		PyErr_Format(PyExc_ValueError, "Autoresize: We expect a tuple with 4 elements");
		return false;
	}
	x = PyObject_IsTrue(PyTuple_GET_ITEM(obj, 0));
	y = PyObject_IsTrue(PyTuple_GET_ITEM(obj, 1));
	w = PyObject_IsTrue(PyTuple_GET_ITEM(obj, 2));
	h = PyObject_IsTrue(PyTuple_GET_ITEM(obj, 3));
	if(PyErr_Occurred())
		return false;
	return true;
}



static
PyObject* guiObject_method_addChild(PyObject* _self, PyObject* _arg) {
	GuiObject* self = (GuiObject*) _self;
	if(!PyType_IsSubtype(Py_TYPE(_arg), &GuiObject_Type)) {
		PyErr_Format(PyExc_ValueError, "GuiObject.addChild: we expect a GuiObject");
		return NULL;
	}
	GuiObject* arg = (GuiObject*) _arg;
	auto func = self->meth_addChild;
	if(!func) {
		PyErr_Format(PyExc_AttributeError, "GuiObject.addChild: must be specified in subclass");
		return NULL;
	}
	Py_BEGIN_ALLOW_THREADS
	func(self, arg);
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef md_addChild = {
	"addChild",
	guiObject_method_addChild,
	METH_O,
	NULL
};


static PyObject* returnObj(PyObject* obj) {
	if(!obj) obj = Py_None;
	Py_INCREF(obj);
	return obj;
}

#define _ReturnAttr(attr) { if(strcmp(key, #attr) == 0) return returnObj(attr); }

#define _ReturnAttrVec(attr) { if(strcmp(key, #attr) == 0) return attr.asPyObject(); }

#define _ReturnCustomAttr(attr) { \
	if(strcmp(key, #attr) == 0) { \
		if(get_ ## attr == 0) { \
			PyErr_Format(PyExc_AttributeError, "GuiObject attribute '%.400s' must be specified in subclass", key); \
			return NULL; \
		} \
		PyThreadState *_save = PyEval_SaveThread(); \
		auto res = (* get_ ## attr)(this); \
		PyEval_RestoreThread(_save); \
		return res.asPyObject(); \
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
		return PyCFunction_New(&md_addChild, (PyObject*) this);
	}

	if(strcmp(key, "__dict__") == 0) {
		if(!__dict__)
			__dict__ = PyDict_New();
		if(!__dict__)
			return NULL;
		return returnObj(__dict__);
	}
	
	// Fallthrough to generic getattr. In case we got another base type, this might work.
	PyObject* s = PyString_FromString(key);
	if(!s) return NULL;
	return PyObject_GenericGetAttr((PyObject*) this, s);
}



#define _SetAttr(attr) { \
	if(strcmp(key, #attr) == 0) { \
		attr = value; \
		Py_INCREF(value); \
		return 0; \
	} }

#define _SetAttrVec(attr) { \
	if(strcmp(key, #attr) == 0) { \
		Vec v; \
		if(!v.initFromPyObject(value)) \
			return -1; \
		attr = v; \
		return 0; \
	} }

#define _SetCustomAttr(attr, ValueType) { \
	if(strcmp(key, #attr) == 0) { \
		if(set_ ## attr == 0) { \
			PyErr_Format(PyExc_AttributeError, "GuiObject attribute '%.400s' must be specified in subclass", key); \
			return -1; \
		} \
		ValueType v; \
		if(!v.initFromPyObject(value)) \
			return -1; \
		Py_BEGIN_ALLOW_THREADS \
		(* set_ ## attr)(this, v); \
		Py_END_ALLOW_THREADS \
		return 0; \
	} }

#define _SetAttr_ErrReadOnly(attr) { \
	if(strcmp(key, #attr) == 0) { \
		PyErr_Format(PyExc_AttributeError, "GuiObject attribute '%.400s' is readonly", key); \
		return -1; \
	} }

int GuiObject::setattr(const char* key, PyObject* value) {
	_SetAttr(root);
	_SetAttr(parent);
	_SetAttr(attr);
	_SetAttr(subjectObject);
	_SetAttr(nativeGuiObject);
	_SetAttrVec(DefaultSpace);
	_SetAttrVec(OuterSpace);
	
	_SetCustomAttr(pos, Vec);
	_SetCustomAttr(size, Vec);
	_SetCustomAttr(autoresize, Autoresize);

	_SetAttr_ErrReadOnly(innerSize);
	_SetAttr_ErrReadOnly(addChild);
	
	// Fallthrough to generic setattr. In case we got another base type, this might work.
	PyObject* s = PyString_FromString(key);
	if(!s) return -1;
	int ret = PyObject_GenericSetAttr((PyObject*) this, s, value);
	Py_XDECREF(s);
	return ret;
}

