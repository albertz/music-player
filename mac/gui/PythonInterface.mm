
// Import Python first. This will define _GNU_SOURCE. This is needed to get strdup (and maybe others). We could also define _GNU_SOURCE ourself, but pyconfig.h from Python has troubles then and redeclares some other stuff. So, to just import Python first is the simplest way.
#include <Python.h>
#include <pythread.h>
#import <Cocoa/Cocoa.h>
#import <AppKit/AppKit.h>
#include <iostream>
#import "AppDelegate.h"
#import "CocoaGuiObject.hpp"
#import "PythonHelpers.h"


static PyObject* CocoaGuiObject_alloc(PyTypeObject *type, Py_ssize_t nitems) {
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
	new ((CocoaGuiObject*) obj) CocoaGuiObject();
	
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

static void CocoaGuiObject_dealloc(PyObject* obj) {
	// This is why we need this custom dealloc: To call the C++ destructor.
	((CocoaGuiObject*) obj)->~CocoaGuiObject();
	Py_TYPE(obj)->tp_free(obj);
}

static int CocoaGuiObject_init(PyObject* self, PyObject* args, PyObject* kwds) {
	return ((CocoaGuiObject*) self)->init(args, kwds);
}

static PyObject* CocoaGuiObject_getattr(PyObject* self, char* key) {
	return ((CocoaGuiObject*) self)->getattr(key);
}

static int CocoaGuiObject_setattr(PyObject* self, char* key, PyObject* value) {
	return ((CocoaGuiObject*) self)->setattr(key, value);
}

// http://docs.python.org/2/c-api/typeobj.html

PyTypeObject CocoaGuiObject_Type = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	"CocoaGuiObject",
	sizeof(CocoaGuiObject),	// basicsize
	0,	// itemsize
	CocoaGuiObject_dealloc,		/*tp_dealloc*/
	0,                  /*tp_print*/
	CocoaGuiObject_getattr,		/*tp_getattr*/
	CocoaGuiObject_setattr,		/*tp_setattr*/
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
	"CocoaGuiObject type", // doc
	0, // tp_traverse
	0, // tp_clear
	0, // tp_richcompare
	offsetof(CocoaGuiObject, weakreflist), // weaklistoffset
	0, // iter
	0, // iternext
	0, // methods
	0, //PlayerMembers, // members
	0, // getset
	0, // base
	0, // dict
	0, // descr_get
	0, // descr_set
	offsetof(CocoaGuiObject, __dict__), // dictoffset
	CocoaGuiObject_init, // tp_init
	CocoaGuiObject_alloc, // alloc
	PyType_GenericNew, // new
};


static AppDelegate* appDelegate = NULL;


PyObject *
guiCocoa_main(PyObject* self) {
	// This is called from Python and replaces the main() control.
	// Basically we do a replacement of NSApplicationMain().
	// For reference: http://www.cocoawithlove.com/2009/01/demystifying-nsapplication-by.html
	
	assert([NSThread isMainThread]);
	
	[NSApplication sharedApplication];
	
	// Note: not needed when bundled...

	// I'm not sure how to get my path name, if we are not bundled...

//	mydir = os.path.dirname(__file__)
//	if os.path.exists(mydir + "/icon.icns"):
//		try:
//			icon = NSImage.alloc().initWithContentsOfFile_(mydir + "/icon.icns")
//		except Exception as e:
//			print "icon.icns failed to load: %s" % e
//		else:
//			if icon:
//				app.setApplicationIconImage_(icon)
//			else:
//				print "icon.icns invalid"
//	else:
//		print "icon.icns not found"

	// Keep own ref to appDelegate because NSApp's ref is only weak.
	// See: http://stackoverflow.com/q/21189168/133374
	appDelegate = [[AppDelegate alloc] init];
	[NSApp setDelegate:appDelegate];

	Py_BEGIN_ALLOW_THREADS
	[NSApp run];
	// We should normally not return from `run`.
	printf("Warning: Returned from NSApp run.\n");
	Py_END_ALLOW_THREADS
	
	PyErr_SetString(PyExc_SystemExit, "return from app run");
	return NULL;
}


PyObject *
guiCocoa_quit(PyObject* self) {
	Py_BEGIN_ALLOW_THREADS
	[NSApp terminate:nil];
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}


PyObject*
guiCocoa_updateControlMenu(PyObject* self) {
	Py_BEGIN_ALLOW_THREADS
	[[NSApp delegate] updateControlMenu];
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}


static PyMethodDef module_methods[] = {
	{"main",	(PyCFunction)guiCocoa_main,	METH_NOARGS,	"overtakes main()"},
	{"quit",	(PyCFunction)guiCocoa_quit,	METH_NOARGS,	"quit application"},
	{"updateControlMenu",	(PyCFunction)guiCocoa_updateControlMenu,	METH_NOARGS,	""},
	{NULL,				NULL}	/* sentinel */
};

PyDoc_STRVAR(module_doc,
"GUI Cocoa implementation.");


PyMODINIT_FUNC
init_guiCocoa(void)
{
	PyEval_InitThreads(); /* Start the interpreter's thread-awareness */

	if(PyType_Ready(&CocoaGuiObject_Type) < 0) {
		Py_FatalError("Can't initialize CocoaGuiObject type");
		return;
	}

	PyObject* m = Py_InitModule3("_guiCocoa", module_methods, module_doc);
	if(!m)
		goto fail;
	
	if(PyModule_AddObject(m, "CocoaGuiObject", (PyObject*) &CocoaGuiObject_Type) != 0)
		goto fail;

	return;

fail:
	if(PyErr_Occurred())
		PyErr_Print();
	
	Py_FatalError("_guiCocoa module init error");
}
