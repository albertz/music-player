
// Import Python first. This will define _GNU_SOURCE. This is needed to get strdup (and maybe others). We could also define _GNU_SOURCE ourself, but pyconfig.h from Python has troubles then and redeclares some other stuff. So, to just import Python first is the simplest way.
#include <Python.h>
#include <pythread.h>

#import <Cocoa/Cocoa.h>
#import <AppKit/AppKit.h>

#import "AppDelegate.h"


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
	//printf("initffmpeg\n");
	PyEval_InitThreads(); /* Start the interpreter's thread-awareness */
	PyObject* m = Py_InitModule3("_guiCocoa", module_methods, module_doc);
	if(!m) {
		Py_FatalError("Can't initialize _guiCocoa module");
		return;
	}
}
