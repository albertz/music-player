

// Import Python first. This will define _GNU_SOURCE. This is needed to get strdup (and maybe others). We could also define _GNU_SOURCE ourself, but pyconfig.h from Python has troubles then and redeclares some other stuff. So, to just import Python first is the simplest way.
#include <Python.h>
#include <pythread.h>

#include "GuiObject.hpp"


static PyObject* guiobject_alloc(PyTypeObject *type, Py_ssize_t nitems) {
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
	new ((GuiObject*) obj) GuiObject();
	
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

static void guiobject_dealloc(PyObject* obj) {
	// This is why we need this custom dealloc: To call the C++ destructor.
	((GuiObject*) obj)->~GuiObject();
	Py_TYPE(obj)->tp_free(obj);
}

static int guiobject_init(PyObject* self, PyObject* args, PyObject* kwds) {
	return ((GuiObject*) self)->init(args, kwds);
}

static PyObject* guiobject_getattr(PyObject* self, char* key) {
	return ((GuiObject*) self)->getattr(key);
}

static int guiobject_setattr(PyObject* self, char* key, PyObject* value) {
	return ((GuiObject*) self)->setattr(key, value);
}

PyTypeObject GuiObject_Type = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	"GuiObject",
	sizeof(GuiObject),	// basicsize
	0,	// itemsize
	guiobject_dealloc,		/*tp_dealloc*/
	0,                  /*tp_print*/
	guiobject_getattr,		/*tp_getattr*/
	guiobject_setattr,		/*tp_setattr*/
	0,                  /*tp_compare*/
	0,					/*tp_repr*/
	0,                  /*tp_as_number*/
	0,                  /*tp_as_sequence*/
	0,                  /*tp_as_mapping*/
	0,					/*tp_hash */
	0, // tp_call
	0, // tp_str
	0, // tp_getattro
	0, // tp_setattro
	0, // tp_as_buffer
	Py_TPFLAGS_HAVE_CLASS, // flags
	"GuiObject type", // doc
	0, // tp_traverse
	0, // tp_clear
	0, // tp_richcompare
	0, // weaklistoffset
	0, // iter
	0, // iternext
	0, // methods
	0, //PlayerMembers, // members
	0, // getset
	0, // base
	0, // dict
	0, // descr_get
	0, // descr_set
	0, /* do we need a dict? */ //offsetof(PlayerObject, dict), // dictoffset
	guiobject_init, // tp_init
	guiobject_alloc, // alloc
	0, // new
};


static PyMethodDef module_methods[] = {
	{NULL,				NULL}	/* sentinel */
};

PyDoc_STRVAR(module_doc,
			 "GUI C++ implementation.");

PyMODINIT_FUNC
init_gui(void) {
	PyEval_InitThreads(); /* Start the interpreter's thread-awareness */

	if (PyType_Ready(&GuiObject_Type) < 0) {
		Py_FatalError("Can't initialize player type");
		return;
	}
	
	PyObject* m = Py_InitModule3("_gui", module_methods, module_doc);
	if(!m) {
		Py_FatalError("Can't initialize _guiCocoa module");
		return;
	}
	
}

