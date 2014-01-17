
// Import Python first. This will define _GNU_SOURCE. This is needed to get strdup (and maybe others). We could also define _GNU_SOURCE ourself, but pyconfig.h from Python has troubles then and redeclares some other stuff. So, to just import Python first is the simplest way.
#include <Python.h>
#include <pythread.h>

#import <Cocoa/Cocoa.h>
#import <AppKit/AppKit.h>

#import "AppDelegate.h"




PyObject *
guiCocoaMain(PyObject* self) {
	// This is called from Python and replaces the main() control.
	// Basically we do a replacement of NSApplicationMain().
	
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

	// I don't quite understand why we need the delegate to be in a variable here.
	// See: http://stackoverflow.com/q/21189168/133374
	AppDelegate* appDelegate = [[AppDelegate alloc] init];
	[NSApp setDelegate:appDelegate];
	[NSApp run];
	
	PyErr_SetString(PyExc_SystemExit, "return from app run");
	return NULL;
}


PyObject *
guiCocoaQuit(PyObject* self) {
	[NSApp terminate:nil];
	Py_INCREF(Py_None);
	return Py_None;
}


static PyMethodDef module_methods[] = {
	{"main",	(PyCFunction)guiCocoaMain,	METH_NOARGS,	"overtakes main()"},
	{"quit",	(PyCFunction)guiCocoaQuit,	METH_NOARGS,	"quit application"},
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
