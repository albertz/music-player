// Copyright (c) Arni Mar Jonsson.
// See LICENSE for details.

// The Python 2/3 compatability code was found in cporting.rst

#include "leveldb_ext.h"

static PyMethodDef leveldb_extension_methods[] =
{
	{ (char*)"RepairDB",  (PyCFunction)pyleveldb_repair_db,  METH_VARARGS, (char*)pyleveldb_repair_db_doc  },
	{ (char*)"DestroyDB", (PyCFunction)pyleveldb_destroy_db, METH_VARARGS, (char*)pyleveldb_destroy_db_doc },
	{NULL, NULL},
};

PyObject* leveldb_exception = 0;

#if PY_MAJOR_VERSION >= 3

struct leveldb_extension_state {
};

static int leveldb_extension_traverse(PyObject* m, visitproc visit, void* arg)
{
	return 0;
}

static int leveldb_extension_clear(PyObject* m)
{
	return 0;
}

static struct PyModuleDef leveldb_extension_def = {
	PyModuleDef_HEAD_INIT,
	"leveldb",
	NULL,
	sizeof(struct leveldb_extension_state),
	leveldb_extension_methods,
	NULL,
	leveldb_extension_traverse,
	leveldb_extension_clear,
	NULL
};

#define INITERROR return NULL

extern "C" PyObject* PyInit_leveldb(void)

#else

#define INITERROR return

extern "C" void initleveldb(void)

#endif
{
#if PY_MAJOR_VERSION >= 3
	PyObject* leveldb_module = PyModule_Create(&leveldb_extension_def);
#else
	PyObject* leveldb_module = Py_InitModule3((char*)"leveldb", leveldb_extension_methods, 0);
#endif

	if (leveldb_module == 0)
		INITERROR;

	// add custom exception
	leveldb_exception = PyErr_NewException((char*)"leveldb.LevelDBError", 0, 0);

	if (leveldb_exception == 0) {
		Py_DECREF(leveldb_module);
		INITERROR;
	}

	if (PyModule_AddObject(leveldb_module, (char*)"LevelDBError", leveldb_exception) != 0) {
		Py_DECREF(leveldb_module);
		INITERROR;
	}

	if (PyType_Ready(&PyLevelDB_Type) < 0) {
		Py_DECREF(leveldb_module);
		INITERROR;
	}

	if (PyType_Ready(&PyLevelDBSnapshot_Type) < 0) {
		Py_DECREF(leveldb_module);
		INITERROR;
	}

	if (PyType_Ready(&PyWriteBatch_Type) < 0) {
		Py_DECREF(leveldb_module);
		INITERROR;
	}

	// add custom types to the different modules
	Py_INCREF(&PyLevelDB_Type);

	if (PyModule_AddObject(leveldb_module, (char*)"LevelDB", (PyObject*)&PyLevelDB_Type) != 0) {
		Py_DECREF(leveldb_module);
		INITERROR;
	}

	Py_INCREF(&PyLevelDBSnapshot_Type);

	if (PyModule_AddObject(leveldb_module, (char*)"Snapshot", (PyObject*)&PyLevelDBSnapshot_Type) != 0) {
		Py_DECREF(leveldb_module);
		INITERROR;
	}

	Py_INCREF(&PyWriteBatch_Type);

	if (PyModule_AddObject(leveldb_module, (char*)"WriteBatch", (PyObject*)&PyWriteBatch_Type) != 0) {
		Py_DECREF(leveldb_module);
		INITERROR;
	}

	PyEval_InitThreads();

	#if PY_MAJOR_VERSION >= 3
	return leveldb_module;
	#endif
}
