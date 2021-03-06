
#include "GuiObject.hpp"
#include "PythonHelpers.h"


int GuiObject::init(PyObject* args, PyObject* kwds) {
	(void)args; // unused
	(void)kwds; // unused
	
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
	PresetSize = Vec(80,80);
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

static
PyObject* guiObject_method_updateContent(PyObject* _self, PyObject* _unused_arg) {
	(void)_unused_arg; // unused
	
	GuiObject* self = (GuiObject*) _self;
	auto func = self->meth_updateContent;
	if(!func) {
		PyErr_Format(PyExc_AttributeError, "GuiObject.updateContent: must be specified in subclass");
		return NULL;
	}
	Py_BEGIN_ALLOW_THREADS
	func(self);
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef md_updateContent = {
	"updateContent",
	guiObject_method_updateContent,
	METH_NOARGS,
	NULL
};


static PyObject* returnObj(PyObject* obj) {
	if(!obj) obj = Py_None;
	Py_INCREF(obj);
	return obj;
}

#define _ReturnAttr(attr) { if(strcmp(key, #attr) == 0) return returnObj((PyObject*) attr); }

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
	_ReturnAttrVec(PresetSize);
	
	_ReturnCustomAttr(pos);
	_ReturnCustomAttr(size);
	_ReturnCustomAttr(innerSize);
	_ReturnCustomAttr(autoresize);
	
	if(strcmp(key, "addChild") == 0) {
		return PyCFunction_New(&md_addChild, (PyObject*) this);
	}

	if(strcmp(key, "updateContent") == 0 && meth_updateContent) {
		return PyCFunction_New(&md_updateContent, (PyObject*) this);
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
	PyObject* ret = PyObject_GenericGetAttr((PyObject*) this, s);
	Py_DECREF(s);
	return ret;
}



#define _SetAttr(attr) { \
	if(strcmp(key, #attr) == 0) { \
		attr = value; \
		Py_INCREF(value); \
		return 0; \
	} }

#define _SetAttrType(attr, ValueType) { \
	if(strcmp(key, #attr) == 0) { \
		if(!PyType_IsSubtype(Py_TYPE(value), & ValueType ## _Type)) { \
			PyErr_Format(PyExc_ValueError, "GuiObject attribute '%.400s' must be of type " #ValueType, key); \
			return -1; \
		} \
		attr = (ValueType*) value; \
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
	_SetAttrType(root, GuiObject);
	_SetAttrType(parent, GuiObject);
	_SetAttr(attr);
	_SetAttr(subjectObject);
	_SetAttr(nativeGuiObject);
	_SetAttrVec(DefaultSpace);
	_SetAttrVec(OuterSpace);
	_SetAttrVec(PresetSize);
	
	_SetCustomAttr(pos, Vec);
	_SetCustomAttr(size, Vec);
	_SetCustomAttr(autoresize, Autoresize);

	_SetAttr_ErrReadOnly(innerSize);
	_SetAttr_ErrReadOnly(addChild);
	//_SetAttr_ErrReadOnly(updateContent); // as long as we have Python code overwriting this
	_SetAttr_ErrReadOnly(__dict__);
	
	// Fallthrough to generic setattr. In case we got another base type, this might work.
	PyObject* s = PyString_FromString(key);
	if(!s) return -1;
	int ret = PyObject_GenericSetAttr((PyObject*) this, s, value);
	Py_DECREF(s);
	return ret;
}


void GuiObject::layout() {
	PyObject* ret = PyObject_CallMethod((PyObject*) this, (char*)"layout", NULL);
	if(!ret) {
		if(PyErr_Occurred()) PyErr_Print();
	}
	Py_XDECREF(ret);
}

Vec GuiObject::setupChilds() {
	Vec sizeVec;
	PyObject* size = PyObject_CallMethod((PyObject*) this, (char*)"setupChilds", NULL);
	if(!size) {
		printf("setupChilds() failed\n");
		if(PyErr_Occurred()) PyErr_Print();
	}
	else if(!sizeVec.initFromPyObject(size)) {
		printf("setupChilds() returned unexpected value (expected is tuple (w,h))\n");
		if(PyErr_Occurred()) PyErr_Print();
	}
	Py_XDECREF(size);
	return sizeVec;
}

void GuiObject::handleCurSelectedSong() {
	// special handling for gui.ctx().curSelectedSong
	PyObject* subj = subjectObject;
	if(!subj) return;
	Py_INCREF(subj);
	PyTypeObject* t = Py_TYPE(subj);
	if(strcmp(t->tp_name, "Song") == 0) {
		PyObject* mod = getModule("gui"); // borrowed ref
		PyObject* ctx = NULL;
		if(!mod) {
			printf("handleCurSelectedSong: cannot get gui module\n");
			goto finalCurSong;
		}
		ctx = PyObject_CallMethod(mod, (char*)"ctx", NULL);
		if(!ctx) {
			printf("handleCurSelectedSong: gui.ctx() failed\n");
			goto finalCurSong;
		}
		PyObject_SetAttrString(ctx, "curSelectedSong", subj);
	finalCurSong:
		if(PyErr_Occurred()) PyErr_Print();
		Py_XDECREF(ctx);
	}
	Py_DECREF(subj);
}

void GuiObject::updateSubjectObject() {
	PyObject* old = NULL;
	std::swap(old, subjectObject);

	if(attr && parent && parent->subjectObject) {
		subjectObject = PyObject_CallMethod(attr, (char*)"__get__", (char*)"(O)", parent->subjectObject);
		if(!subjectObject) {
			if(PyErr_Occurred()) PyErr_Print();
		}
		if(subjectObject == Py_None)
			Py_CLEAR(subjectObject);
	}
	
	Py_CLEAR(old);
}
