//
//  FunctionWrapper.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include "FunctionWrapper.hpp"


static PyObject* FunctionWrapper_alloc(PyTypeObject *type, Py_ssize_t nitems) {
    PyObject *obj;
    const size_t size = _PyObject_VAR_SIZE(type, nitems+1);
    /* note that we need to add one, for the sentinel */
	
    if (PyType_IS_GC(type))
        obj = _PyObject_GC_Malloc(size);
    else
        obj = (PyObject *)PyObject_MALLOC(size);
	
    if (obj == NULL)
        return PyErr_NoMemory();
	
	// This is why we need this custom alloc: To call the C++ constructor.
    memset(obj, '\0', size);
	new ((FunctionWrapper*) obj) FunctionWrapper();
	
    if (type->tp_flags & Py_TPFLAGS_HEAPTYPE)
        Py_INCREF(type);
	
    if (type->tp_itemsize == 0)
        PyObject_INIT(obj, type);
    else
        (void) PyObject_INIT_VAR((PyVarObject *)obj, type, nitems);
	
    if (PyType_IS_GC(type))
        _PyObject_GC_TRACK(obj);
    return obj;
}

static void FunctionWrapper_dealloc(PyObject* obj) {
	FunctionWrapper* wrapper = (FunctionWrapper*) obj;
	if(wrapper->weakrefs)
		PyObject_ClearWeakRefs(obj);
	wrapper->~FunctionWrapper();
	Py_TYPE(obj)->tp_free(obj);
}


static PyObject* FunctionWrapper_call(PyObject* obj, PyObject* args, PyObject* kw) {
	PyCallback func = ((FunctionWrapper*)obj)->func;
	if(!func) {
		PyErr_Format(PyExc_ValueError, "FunctionWrapper: function is not set");
		return NULL;
	}
	return func(args, kw);
}

PyTypeObject FunctionWrapper_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "FunctionWrapper",
    sizeof(FunctionWrapper),
    0,
    FunctionWrapper_dealloc,                   /* tp_dealloc */
    0,                                          /* tp_print */
    0,                                          /* tp_getattr */
    0,                                          /* tp_setattr */
    0,											/* tp_compare */
    0,											/* tp_repr */
    0,                                          /* tp_as_number */
    0,                                          /* tp_as_sequence */
    0,                                          /* tp_as_mapping */
    0,											/* tp_hash */
    FunctionWrapper_call,                       /* tp_call */
    0,                                          /* tp_str */
    0,											/* tp_getattro */
    0,                                          /* tp_setattro */
    0,                                          /* tp_as_buffer */
    Py_TPFLAGS_HAVE_CLASS | Py_TPFLAGS_HAVE_WEAKREFS,/* tp_flags */
    0,                                          /* tp_doc */
    0,											/* tp_traverse */
    0,											/* tp_clear */
    0,                                           /* tp_richcompare */
    offsetof(FunctionWrapper, weakrefs),        /* tp_weaklistoffset */
    0,                                          /* tp_iter */
    0,                                          /* tp_iternext */
    0,                                          /* tp_methods */
    0,											/* tp_members */
    0,											/* tp_getset */
    0,                                          /* tp_base */
    0,                                          /* tp_dict */
	0,					/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	0,					/* tp_init */
	FunctionWrapper_alloc,			/* tp_alloc */
	PyType_GenericNew,				/* tp_new */
};

FunctionWrapper* newFunctionWrapper(PyCallback func) {
	if(!func) {
		PyErr_Format(PyExc_ValueError, "newFunctionWrapper: func must not be NULL");
		return NULL;
	}
	if(PyType_Ready(&FunctionWrapper_Type) < 0) {
		PyErr_Format(PyExc_SystemError, "failed to init FunctionWrapper_Type");
		return NULL;
	}
	PyObject* res = PyObject_CallObject((PyObject*) &FunctionWrapper_Type, NULL);
	if(!res) return NULL;
	if(!PyType_IsSubtype(Py_TYPE(res), &FunctionWrapper_Type)) {
		PyErr_Format(PyExc_SystemError, "FunctionWrapper constructs invalid object");
		Py_DECREF(res);
		return NULL;
	}
	FunctionWrapper* wrapper = (FunctionWrapper*) res;
	wrapper->func = func;
	return wrapper;
}
