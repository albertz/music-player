//
//  debugger.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 03.08.13.
//  This code is under the 2-clause BSD license, see License.txt in the root directory of this project.
//

#include <Python.h>
#include "debugger.h"

PyDoc_STRVAR(module_doc,
	"debugger module.");

static PyMethodDef module_methods[] = {
    {NULL, NULL}  /* sentinel */
};

PyMODINIT_FUNC
#if PY_MAJOR_VERSION >= 3
PyInit_debugger(void)
#else
initdebugger(void)
#endif
{
    PyObject *m;
	
#if PY_MAJOR_VERSION >= 3
    m = PyModule_Create(&module_def);
#else
    m = Py_InitModule3("debugger", module_methods, module_doc);
#endif
    if (m == NULL) {
#if PY_MAJOR_VERSION >= 3
        return NULL;
#else
        return;
#endif
    }
	
#if PY_MAJOR_VERSION >= 3
    return m;
#else
    return;
#endif
	
error:
#if PY_MAJOR_VERSION >= 3
    Py_DECREF(m);
    return NULL;
#else
    return;
#endif
}
