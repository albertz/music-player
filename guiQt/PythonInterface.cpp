
// Import Python first. This will define _GNU_SOURCE. This is needed to get strdup (and maybe others). We could also define _GNU_SOURCE ourself, but pyconfig.h from Python has troubles then and redeclares some other stuff. So, to just import Python first is the simplest way.
#include <Python.h>
#include <pythread.h>
#include <iostream>
#include "QtApp.hpp"
#include "PyQtGuiObject.hpp"
#include "PythonHelpers.h"
#include "PyUtils.h"
#include "PyThreading.hpp"
#include "Builders.hpp"
#include "FunctionWrapper.hpp"
#include "QtMenu.hpp"


static PyObject* QtGuiObject_alloc(PyTypeObject *type, Py_ssize_t nitems) {
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
	new ((PyQtGuiObject*) obj) PyQtGuiObject();
	
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

static void QtGuiObject_dealloc(PyObject* obj) {
	// This is why we need this custom dealloc: To call the C++ destructor.
	((PyQtGuiObject*) obj)->~PyQtGuiObject();
	Py_TYPE(obj)->tp_free(obj);
}

static int QtGuiObject_init(PyObject* self, PyObject* args, PyObject* kwds) {
	return ((PyQtGuiObject*) self)->init(args, kwds);
}

static PyObject* QtGuiObject_getattr(PyObject* self, char* key) {
	return ((PyQtGuiObject*) self)->getattr(key);
}

static int QtGuiObject_setattr(PyObject* self, char* key, PyObject* value) {
	return ((PyQtGuiObject*) self)->setattr(key, value);
}

// http://docs.python.org/2/c-api/typeobj.html

PyTypeObject QtGuiObject_Type = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	"QtGuiObject",
	sizeof(PyQtGuiObject),	// basicsize
	0,	// itemsize
	QtGuiObject_dealloc,		/*tp_dealloc*/
	0,                  /*tp_print*/
	QtGuiObject_getattr,		/*tp_getattr*/
	QtGuiObject_setattr,		/*tp_setattr*/
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
	Py_TPFLAGS_HAVE_CLASS|Py_TPFLAGS_HAVE_WEAKREFS|Py_TPFLAGS_HAVE_GC, // flags
	"QtGuiObject type", // doc
	0, // tp_traverse
	0, // tp_clear
	0, // tp_richcompare
	offsetof(PyQtGuiObject, weakreflist), // weaklistoffset
	0, // iter
	0, // iternext
	0, // methods
	0, //PlayerMembers, // members
	0, // getset
	0, // base
	0, // dict
	0, // descr_get
	0, // descr_set
	offsetof(PyQtGuiObject, __dict__), // dictoffset
	QtGuiObject_init, // tp_init
	QtGuiObject_alloc, // alloc
	PyType_GenericNew, // new
};



PyObject *
guiQt_main(PyObject* self) {
	(void)self;
	// This is called from Python and replaces the main() control.
	
	// It might make sense to assert that we are the main thread.
	// However, there is no good cross-platform way to do this (afaik).
	// We could use Python... For now, we just hope that Qt behaves sane.
	// Anyway, on the Python side, we should have called this
	// in the main thread.
	
	PyObject* guiMod = getModule("gui"); // borrowed
	if(!guiMod) {
		PyErr_Format(PyExc_SystemError, "guiQt.main: gui module not found");
		return NULL;
	}
	
	int ret = 0;
	Py_BEGIN_ALLOW_THREADS
	// Keep it static. Noone should access it when we return
	// from here, but I like to be safe anyway.
	static QtApp app;
	
	{
		PyScopedGIL gil;	
		PyObject* init1 = PyObject_CallMethod(guiMod, (char*)"_initPre", NULL);
		if(!init1) return NULL;
		Py_DECREF(init1);
	}
	
	setupMenu();
	app.openMainWindow();
	
	{	
		PyScopedGIL gil;	
		PyObject* init2 = PyObject_CallMethod(guiMod, (char*)"_initPost", NULL);
		if(!init2) return NULL;
		Py_DECREF(init2);
	}
	
	// Enter the Qt main event loop.
	ret = app.exec();
	// Note that it depends on the Qt backend whether we return here or not.
	Py_END_ALLOW_THREADS
	
	PyErr_SetObject(PyExc_SystemExit, PyInt_FromLong(ret));
	return NULL;
}


PyObject *
guiQt_quit(PyObject* self) {
	(void)self;
	Py_BEGIN_ALLOW_THREADS
	qApp->quit();
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}


PyObject*
guiQt_updateControlMenu(PyObject* self) {
	(void)self;
	Py_BEGIN_ALLOW_THREADS
	//[[NSApp delegate] updateControlMenu];
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}


PyObject*
pyBuildControl(const std::string& controlType, ControlBuilderFunc builderFunc, PyObject* args, PyObject* kws) {
	PyObject* control = NULL;
	if(!PyArg_ParseTuple(args, ("O:buildControl" + controlType).c_str(), &control))
		return NULL;
	if(!PyType_IsSubtype(Py_TYPE(control), &QtGuiObject_Type)) {
		PyErr_Format(PyExc_ValueError, "guiQt.buildControl%s: we expect a QtGuiObject", controlType.c_str());
		return NULL;
	}
	PyQtGuiObject* guiObject = (PyQtGuiObject*) control;
	bool res = builderFunc(guiObject);
	if(!res)
		// XXX: handle somehow? ...
		printf("guiQt.buildControl%s: warning, returned error\n", controlType.c_str());
	
	Py_INCREF(control);
	return control;
}

PyObject*
guiQt_buildControl(PyObject* self, PyObject* args, PyObject* kws) {
	(void)self;
	PyObject* userAttr = NULL;
	PyQtGuiObject* parent = NULL;
	static const char *kwlist[] = {"userAttr", "parent", NULL};
	if(!PyArg_ParseTupleAndKeywords(
			args, kws, "OO:buildControl", (char**)kwlist,
			&userAttr, &parent))
		return NULL;

	if(!PyType_IsSubtype(Py_TYPE(parent), &QtGuiObject_Type)) {
		PyErr_Format(PyExc_ValueError, "guiQt.buildControl: parent must be a QtGuiObject");
		return NULL;
	}

	if(parent->root == NULL) {
		PyErr_Format(PyExc_ValueError, "guiQt.buildControl: parent.root is NULL");
		return NULL;		
	}
	
	if(parent->subjectObject == NULL) {
		PyErr_Format(PyExc_ValueError, "guiQt.buildControl: parent.subjectObject is NULL");
		return NULL;		
	}
	
	std::string controlType;
	{
		PyObject* typeClass = PyObject_CallMethod(userAttr, (char*)"getTypeClass", NULL);
		if(!typeClass) return NULL;
		PyObject* typeClassName = PyObject_GetAttrString(typeClass, "__name__");
		if(!typeClassName) { Py_DECREF(typeClass); return NULL; }
		if(!pyStr(typeClassName, controlType)) { Py_DECREF(typeClass); Py_DECREF(typeClassName); return NULL; }
		PyObject* traitsMod = getModule("Traits"); // borrowed
		if(!traitsMod) {
			PyErr_Format(PyExc_ValueError, "guiQt.buildControl: Traits module not found");
			Py_DECREF(typeClass); Py_DECREF(typeClassName);
			return NULL;
		}
		PyObject* traitsClass = PyObject_GetAttrString(traitsMod, controlType.c_str());
		if(!traitsClass) {
			PyErr_Format(PyExc_ValueError, "guiQt.buildControl: Traits.%s not found", controlType.c_str());
			Py_DECREF(typeClass); Py_DECREF(typeClassName);
			return NULL;
		}
		if(traitsClass != typeClass) {
			PyErr_Format(PyExc_ValueError, "guiQt.buildControl: Traits.%s is different class", controlType.c_str());
			Py_DECREF(typeClass); Py_DECREF(typeClassName); Py_DECREF(traitsClass);
			return NULL;
		}
		Py_DECREF(typeClass);
		Py_DECREF(typeClassName);
		Py_DECREF(traitsClass);		
	}
	ControlBuilderFunc builderFunc = getControlBuilder(controlType);
	if(!builderFunc) {
		PyErr_Format(PyExc_NotImplementedError, "guiQt.buildControl: %s-widget not implemented yet", controlType.c_str());
		return NULL;
	}
	
	PyQtGuiObject* control = (PyQtGuiObject*) PyObject_CallFunction((PyObject*) &QtGuiObject_Type, NULL);
	if(!control) return NULL;
	
	assert(control->root == NULL);
	control->root = parent->root;
	Py_XINCREF(control->root);
	assert(control->parent == NULL);
	control->parent = parent;
	Py_XINCREF(control->parent);
	assert(control->attr == NULL);
	control->attr = userAttr;
	Py_XINCREF(control->attr);
	
	assert(control->subjectObject == NULL);
	control->subjectObject = PyObject_CallMethod(userAttr, (char*)"__get__", (char*)"(O)", parent->subjectObject);
	if(control->subjectObject == NULL) {
		Py_DECREF(control);
		return NULL;
	}
	
	{
		PyScopedGIUnlock gunlock;
		execInMainThread_sync([&]() {
			bool res = builderFunc(control);
			if(!res)
				// XXX: handle somehow? ...
				printf("guiQt.buildControl: warning, returned error\n");		
		});
	}
	
	// forward control
	return (PyObject*) control;
}



static PyMethodDef module_methods[] = {
	{"main",	(PyCFunction)guiQt_main,	METH_NOARGS,	"overtakes main()"},
	{"quit",	(PyCFunction)guiQt_quit,	METH_NOARGS,	"quit application"},
	{"updateControlMenu",	(PyCFunction)guiQt_updateControlMenu,	METH_NOARGS,	""},
	{"buildControl",  (PyCFunction)guiQt_buildControl, METH_VARARGS|METH_KEYWORDS, ""},
	{NULL,				NULL}	/* sentinel */
};

PyDoc_STRVAR(module_doc,
"GUI Qt implementation.");


PyMODINIT_FUNC
initguiQt(void) {
	PyEval_InitThreads(); /* Start the interpreter's thread-awareness */

	if(PyType_Ready(&QtGuiObject_Type) < 0) {
		Py_FatalError("Can't initialize QtGuiObject type");
		return;
	}

	PyObject* m = Py_InitModule3("guiQt", module_methods, module_doc);
	if(!m) {
		Py_FatalError("Can't initialize guiQt module");
		return;		
	}
	
	bool fail = false;

	if(PyModule_AddObject(m, "QtGuiObject", (PyObject*) &QtGuiObject_Type) != 0)
		fail = true;

	iterControlTypes([&](const std::string& controlType, ControlBuilderFunc builderFunc) {
		struct PythonWrapper {
			std::string controlType;
			ControlBuilderFunc builderFunc;
			PyObject* operator()(PyObject* args, PyObject* kw) {
				return pyBuildControl(controlType, builderFunc, args, kw);
			}
		};
		PythonWrapper wrapper;
		wrapper.controlType = controlType;
		wrapper.builderFunc = builderFunc;
		PyObject* funcObj = (PyObject*) newFunctionWrapper(wrapper);
		if(!funcObj) {
			fail = true;
			return;
		}
		if(PyModule_AddObject(m, ("builControl" + controlType).c_str(), funcObj) != 0)
			fail = true;
	});

	if(fail) {
		if(PyErr_Occurred())
			PyErr_Print();
		
		Py_FatalError("guiQt module init error");
	}
}
