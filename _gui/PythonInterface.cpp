

// Import Python first. This will define _GNU_SOURCE. This is needed to get strdup (and maybe others). We could also define _GNU_SOURCE ourself, but pyconfig.h from Python has troubles then and redeclares some other stuff. So, to just import Python first is the simplest way.
#include <Python.h>
#include <pythread.h>



static PyMethodDef module_methods[] = {
	{NULL,				NULL}	/* sentinel */
};

PyDoc_STRVAR(module_doc,
			 "GUI C++ implementation.");

PyMODINIT_FUNC
init_guiCocoa(void) {
	PyEval_InitThreads(); /* Start the interpreter's thread-awareness */
	PyObject* m = Py_InitModule3("_gui", module_methods, module_doc);
	if(!m) {
		Py_FatalError("Can't initialize _guiCocoa module");
		return;
	}

	
}

