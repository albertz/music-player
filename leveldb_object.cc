// Copyright (c) Arni Mar Jonsson.
// See LICENSE for details.

#include "leveldb_ext.h"

#include <leveldb/comparator.h>

static PyObject* PyLevelDBIter_New(PyObject* ref, PyLevelDB* db, leveldb::Iterator* iterator, std::string* bound, int include_value, int is_reverse);
static PyObject* PyLevelDBSnapshot_New(PyLevelDB* db, const leveldb::Snapshot* snapshot);

static void PyLevelDB_set_error(leveldb::Status& status)
{
	PyErr_SetString(leveldb_exception, status.ToString().c_str());
}

const char pyleveldb_repair_db_doc[] =
"leveldb.RepairDB(db_dir)\n\nAttempts to recover as much data as possible from a corrupt database."
;
extern PyObject* pyleveldb_repair_db(PyLevelDB* self, PyObject* args)
{
	const char* db_dir = 0;

	if (!PyArg_ParseTuple(args, (char*)"s", &db_dir))
		return 0;

	std::string _db_dir(db_dir);
	leveldb::Status status;
	leveldb::Options options;

	Py_BEGIN_ALLOW_THREADS
	status = leveldb::RepairDB(_db_dir.c_str(), options);
	Py_END_ALLOW_THREADS

	if (!status.ok()) {
		PyLevelDB_set_error(status);
		return 0;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

const char pyleveldb_destroy_db_doc[] =
"leveldb.DestroyDB(db_dir)\n\nAttempts to recover as much data as possible from a corrupt database."
;
extern PyObject* pyleveldb_destroy_db(PyObject* self, PyObject* args)
{
	const char* db_dir = 0;

	if (!PyArg_ParseTuple(args, (char*)"s", &db_dir))
		return 0;

	std::string _db_dir(db_dir);
	leveldb::Status status;
	leveldb::Options options;

	Py_BEGIN_ALLOW_THREADS
	status = leveldb::DestroyDB(_db_dir.c_str(), options);
	Py_END_ALLOW_THREADS

	if (!status.ok()) {
		PyLevelDB_set_error(status);
		return 0;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static void PyLevelDB_dealloc(PyLevelDB* self)
{
	Py_BEGIN_ALLOW_THREADS
	delete self->_db;
	delete self->_options;
	delete self->_cache;

	if (self->_comparator != leveldb::BytewiseComparator())
		delete self->_comparator;

	Py_END_ALLOW_THREADS

	self->_db = 0;
	self->_options = 0;
	self->_cache = 0;
	self->_comparator = 0;
	self->n_iterators = 0;
	self->n_snapshots = 0;

	#if PY_MAJOR_VERSION >= 3
	Py_TYPE(self)->tp_free((PyObject*)self);
	#else
	((PyObject*)self)->ob_type->tp_free((PyObject*)self);
	#endif
}

static void PyLevelDBSnapshot_dealloc(PyLevelDBSnapshot* self)
{
	if (self->db && self->snapshot) {
		Py_BEGIN_ALLOW_THREADS
		self->db->_db->ReleaseSnapshot(self->snapshot);
		Py_END_ALLOW_THREADS
	}

	if (self->db)
		self->db->n_snapshots -= 1;

	Py_DECREF(self->db);
	self->db = 0;
	self->snapshot = 0;

	#if PY_MAJOR_VERSION >= 3
	Py_TYPE(self)->tp_free((PyObject*)self);
	#else
	((PyObject*)self)->ob_type->tp_free((PyObject*)self);
	#endif
}

static void PyWriteBatch_dealloc(PyWriteBatch* self)
{
	delete self->ops;

	#if PY_MAJOR_VERSION >= 3
	Py_TYPE(self)->tp_free((PyObject*)self);
	#else
	((PyObject*)self)->ob_type->tp_free((PyObject*)self);
	#endif
}

static PyObject* PyLevelDB_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
	PyLevelDB* self = (PyLevelDB*)type->tp_alloc(type, 0);

	if (self) {
		self->_db = 0;
		self->_options = 0;
		self->_cache = 0;
		self->_comparator = 0;
		self->n_iterators = 0;
		self->n_snapshots = 0;
	}

	return (PyObject*)self;
}

static PyObject* PyWriteBatch_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
	PyWriteBatch* self = (PyWriteBatch*)type->tp_alloc(type, 0);

	if (self) {
		self->ops = new std::vector<PyWriteBatchEntry>;

		if (self->ops == 0) {
			#if PY_MAJOR_VERSION >= 3
			Py_TYPE(self)->tp_free((PyObject*)self);
			#else
			((PyObject*)self)->ob_type->tp_free((PyObject*)self);
			#endif
			return PyErr_NoMemory();
		}
	}

	return (PyObject*)self;
}

static PyObject* PyLevelDBSnapshot_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
	PyLevelDBSnapshot* self = (PyLevelDBSnapshot*)type->tp_alloc(type, 0);

	if (self) {
		self->db = 0;
		self->snapshot = 0;
	}

	return (PyObject*)self;
}

// Python 2.6+
#if PY_MAJOR_VERSION >= 3 || (PY_MAJOR_VERSION >= 2 && PY_MINOR_VERSION >= 6)
#define PY_LEVELDB_DEFINE_BUFFER(n) Py_buffer n; (n).buf = 0; (n).len = 0; (n).obj = 0
#define PY_LEVELDB_RELEASE_BUFFER(n) if (n.obj) {PyBuffer_Release(&n);}
#define PARAM_V(n) &(n)
#define PY_LEVELDB_BEGIN_ALLOW_THREADS Py_BEGIN_ALLOW_THREADS
#define PY_LEVELDB_END_ALLOW_THREADS Py_END_ALLOW_THREADS
#define PY_LEVELDB_SLICE(n) leveldb::Slice n##_slice((const char*)(n).buf, (size_t)(n).len)
#define PY_LEVELDB_STRING(n) std::string((const char*)(n).buf, (size_t)(n).len)

#if PY_MAJOR_VERSION >= 3
	#define PARAM_S "y*"
	#define PY_LEVELDB_STRING_OR_BYTEARRAY PyByteArray_FromStringAndSize
#else
	#define PARAM_S "s*"
	#define PY_LEVELDB_STRING_OR_BYTEARRAY PyString_FromStringAndSize
#endif

// Python 2.4/2.5
#else
#define PY_LEVELDB_DEFINE_BUFFER(n) const char* s_##n = 0; int n_##n
#define PY_LEVELDB_RELEASE_BUFFER(n)
#define PARAM_V(n) &s_##n, &n_##n
#define PY_LEVELDB_BEGIN_ALLOW_THREADS
#define PY_LEVELDB_END_ALLOW_THREADS
#define PY_LEVELDB_SLICE(n) leveldb::Slice n##_slice((const char*)s_##n, (size_t)n_##n)
#define PY_LEVELDB_STRING(n) std::string((const char*)s_##n, (size_t)n_##n);

#define PARAM_S "t#"
#define PY_LEVELDB_STRING_OR_BYTEARRAY PyString_FromStringAndSize
#endif

class PythonComparatorWrapper : public leveldb::Comparator {

public:

	PythonComparatorWrapper(const char* name, PyObject* comparator) :
		name(name),
		comparator(comparator),
		last_exception_type(0),
		last_exception_value(0),
		last_exception_traceback(0)
	{
		Py_INCREF(comparator);
		#if PY_MAJOR_VERSION >= 3
		zero = PyLong_FromLong(0);
		#else
		zero = PyInt_FromLong(0);
		#endif
	}

	~PythonComparatorWrapper()
	{
		Py_DECREF(comparator);
		Py_XDECREF(last_exception_type);
		Py_XDECREF(last_exception_value);
		Py_XDECREF(last_exception_traceback);
		Py_XDECREF(zero);
	}

private:

	int GetSign(PyObject* i, int* c) const
	{
		#if PY_MAJOR_VERSION >= 3
		if (PyLong_Check(i)) {
		#else
		if (PyInt_Check(i) || PyLong_Check(i)) {
		#endif
			#if PY_MAJOR_VERSION >= 3
			if (PyObject_RichCompareBool(i, zero, Py_LT))
				*c = -1;
			else if (PyObject_RichCompareBool(i, zero, Py_GT))
				*c = 1;
			else
				*c = 0;
			#else
			*c = PyObject_Compare(i, zero);
			#endif

			if (PyErr_Occurred())
				return 0;

			return 1;
		}

		PyErr_SetString(PyExc_TypeError, "comparison value is not an integer");
		return 0;
	}

	void SetError() const
	{
		// we don't do too much
		fprintf(stderr, "py-leveldb: Python comparison failure. Unable to reliably continue. Goodbye cruel world.\n\n");
		PyErr_Print();
		fflush(stderr);
		abort();

//		assert(PyErr_Occurred());
//		Py_XDECREF(last_exception_type);
//		Py_XDECREF(last_exception_value);
//		Py_XDECREF(last_exception_traceback);
//		PyErr_Fetch(&last_exception_type, &last_exception_value, &last_exception_value);
	}

public:

//	bool CheckAndSetError()
//	{
//		if (last_exception_type) {
//			PyErr_Restore(last_exception_type, last_exception_value, last_exception_traceback);
//			last_exception_type = 0;
//			last_exception_value = 0;
//			last_exception_traceback = 0;
//			return true;
//		}
//
//		return false;
//	}

	// this can be called from pretty much any leveldb threads
	int Compare(const leveldb::Slice& a, const leveldb::Slice& b) const
	{
		// http://docs.python.org/dev/c-api/init.html#non-python-created-threads
		PyGILState_STATE gstate;
		gstate = PyGILState_Ensure();

		// acquire python thread
		PyObject* a_ = PY_LEVELDB_STRING_OR_BYTEARRAY(a.data(), a.size());
		PyObject* b_ = PY_LEVELDB_STRING_OR_BYTEARRAY(b.data(), b.size());

		if (a_ == 0 || b_ == 0) {
			Py_XDECREF(a_);
			Py_XDECREF(b_);
			SetError();
			PyGILState_Release(gstate);
			return 0;
		}

		PyObject* c = PyObject_CallFunctionObjArgs(comparator, a_, b_, 0);
		int cmp = 0;

		Py_XDECREF(a_);
		Py_XDECREF(b_);

		if (c == 0 || !GetSign(c, &cmp))
			SetError();

		PyGILState_Release(gstate);
		return cmp;
	}

	const char* Name() const
	{
		return name.c_str();
	}

	void FindShortestSeparator(std::string*, const leveldb::Slice&) const { }
	void FindShortSuccessor(std::string*) const { }

private:

	std::string name;
	PyObject* comparator;
	PyObject* last_exception_type;
	PyObject* last_exception_value;
	PyObject* last_exception_traceback;
	PyObject* zero;
};


static PyObject* PyLevelDB_Put(PyLevelDB* self, PyObject* args, PyObject* kwds)
{
	const char* kwargs[] = {"key", "value", "sync", 0};
	PyObject* sync = Py_False;

	PY_LEVELDB_DEFINE_BUFFER(key);
	PY_LEVELDB_DEFINE_BUFFER(value);

	leveldb::WriteOptions options;
	leveldb::Status status;

	if (!PyArg_ParseTupleAndKeywords(args, kwds, (char*)PARAM_S PARAM_S "|O!", (char**)kwargs, PARAM_V(key), PARAM_V(value), &PyBool_Type, &sync))
		return 0;

	PY_LEVELDB_BEGIN_ALLOW_THREADS

	PY_LEVELDB_SLICE(key);
	PY_LEVELDB_SLICE(value);

	options.sync = (sync == Py_True) ? true : false;
	status = self->_db->Put(options, key_slice, value_slice);

	PY_LEVELDB_END_ALLOW_THREADS

	PY_LEVELDB_RELEASE_BUFFER(key);
	PY_LEVELDB_RELEASE_BUFFER(value);

	if (!status.ok()) {
		PyLevelDB_set_error(status);
		return 0;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* PyLevelDB_Get_(PyLevelDB* self, leveldb::DB* db, const leveldb::Snapshot* snapshot, PyObject* args, PyObject* kwds)
{
	PyObject* verify_checksums = Py_False;
	PyObject* fill_cache = Py_True;
	PyObject* failobj = 0;

	const char* kwargs[] = {"key", "verify_checksums", "fill_cache", "default", 0};

	leveldb::Status status;
	std::string value;

	PY_LEVELDB_DEFINE_BUFFER(key);

	if (!PyArg_ParseTupleAndKeywords(args, kwds, (char*)PARAM_S "|O!O!O", (char**)kwargs, PARAM_V(key), &PyBool_Type, &verify_checksums, &PyBool_Type, &fill_cache, &failobj))
		return 0;

	PY_LEVELDB_BEGIN_ALLOW_THREADS

	PY_LEVELDB_SLICE(key);

	leveldb::ReadOptions options;
	options.verify_checksums = (verify_checksums == Py_True) ? true : false;
	options.fill_cache = (fill_cache == Py_True) ? true : false;
	options.snapshot = snapshot;

	status = db->Get(options, key_slice, &value);

	PY_LEVELDB_END_ALLOW_THREADS

	PY_LEVELDB_RELEASE_BUFFER(key);

	if (status.IsNotFound()) {
		if (failobj) {
			Py_INCREF(failobj);
			return failobj;
		}

		PyErr_SetNone(PyExc_KeyError);
		return 0;
	}

	if (!status.ok()) {
		PyLevelDB_set_error(status);
		return 0;
	}

	return PY_LEVELDB_STRING_OR_BYTEARRAY(value.c_str(), value.length());
}

static PyObject* PyLevelDB_Get(PyLevelDB* self, PyObject* args, PyObject* kwds)
{
	return PyLevelDB_Get_(self, self->_db, 0, args, kwds);
}

static PyObject* PyLevelDBSnaphot_Get(PyLevelDBSnapshot* self, PyObject* args, PyObject* kwds)
{
	return PyLevelDB_Get_(self->db, self->db->_db, self->snapshot, args, kwds);
}

static PyObject* PyLevelDB_Delete(PyLevelDB* self, PyObject* args, PyObject* kwds)
{
	PyObject* sync = Py_False;
	const char* kwargs[] = {"key", "sync", 0};

	PY_LEVELDB_DEFINE_BUFFER(key);	

	leveldb::Status status;

	if (!PyArg_ParseTupleAndKeywords(args, kwds, (char*)PARAM_S "|O!", (char**)kwargs, PARAM_V(key), &PyBool_Type, &sync))
		return 0;

	PY_LEVELDB_BEGIN_ALLOW_THREADS

	PY_LEVELDB_SLICE(key);

	leveldb::WriteOptions options;
	options.sync = (sync == Py_True) ? true : false;

	status = self->_db->Delete(options, key_slice);

	PY_LEVELDB_END_ALLOW_THREADS

	PY_LEVELDB_RELEASE_BUFFER(key);

	if (!status.ok()) {
		PyLevelDB_set_error(status);
		return 0;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* PyWriteBatch_Put(PyWriteBatch* self, PyObject* args)
{
	// NOTE: we copy all buffers
	PY_LEVELDB_DEFINE_BUFFER(key);
	PY_LEVELDB_DEFINE_BUFFER(value);

	if (!PyArg_ParseTuple(args, (char*)PARAM_S PARAM_S, PARAM_V(key), PARAM_V(value)))
		return 0;

	PyWriteBatchEntry op;
	op.is_put = true;

	PY_LEVELDB_BEGIN_ALLOW_THREADS

	PY_LEVELDB_SLICE(key);
	PY_LEVELDB_SLICE(value);

	op.key = PY_LEVELDB_STRING(key);
	op.value = PY_LEVELDB_STRING(value);

	PY_LEVELDB_END_ALLOW_THREADS

	PY_LEVELDB_RELEASE_BUFFER(key);
	PY_LEVELDB_RELEASE_BUFFER(value);

	self->ops->push_back(op);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* PyWriteBatch_Delete(PyWriteBatch* self, PyObject* args)
{
	// NOTE: we copy all buffers
	PY_LEVELDB_DEFINE_BUFFER(key);

	if (!PyArg_ParseTuple(args, (char*)PARAM_S, PARAM_V(key)))
		return 0;

	PyWriteBatchEntry op;
	op.is_put = false;

	PY_LEVELDB_BEGIN_ALLOW_THREADS

	op.key = PY_LEVELDB_STRING(key);

	PY_LEVELDB_END_ALLOW_THREADS

	PY_LEVELDB_RELEASE_BUFFER(key);

	self->ops->push_back(op);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* PyLevelDB_Write(PyLevelDB* self, PyObject* args, PyObject* kwds)
{
	PyWriteBatch* write_batch = 0;
	PyObject* sync = Py_False;
	const char* kwargs[] = {"write_batch", "sync", 0};

	if (!PyArg_ParseTupleAndKeywords(args, kwds, (char*)"O!|O!", (char**)kwargs, &PyWriteBatch_Type, &write_batch, &PyBool_Type, &sync))
		return 0;

	leveldb::WriteOptions options;
	options.sync = (sync == Py_True) ? true : false;
	leveldb::WriteBatch batch;
	leveldb::Status status;

	for (size_t i = 0; i < write_batch->ops->size(); i++) {
		PyWriteBatchEntry& op = (*write_batch->ops)[i];
		leveldb::Slice key(op.key.c_str(), op.key.size());
		leveldb::Slice value(op.value.c_str(), op.value.size());

		if (op.is_put) {
			batch.Put(key, value);
		} else {
			batch.Delete(key);
		}
	}

	Py_BEGIN_ALLOW_THREADS
	status = self->_db->Write(options, &batch);
	Py_END_ALLOW_THREADS

	if (!status.ok()) {
		PyLevelDB_set_error(status);
		return 0;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* PyLevelDB_RangeIter_(PyLevelDB* self, const leveldb::Snapshot* snapshot, PyObject* args, PyObject* kwds)
{
	int is_from = 0;
	int is_to = 0;
	PY_LEVELDB_DEFINE_BUFFER(a);
	PY_LEVELDB_DEFINE_BUFFER(b);
	PyObject* _a = Py_None;
	PyObject* _b = Py_None;
	PyObject* verify_checksums = Py_False;
	PyObject* fill_cache = Py_True;
	PyObject* include_value = Py_True;
	PyObject* is_reverse = Py_False;
	const char* kwargs[] = {"key_from", "key_to", "verify_checksums", "fill_cache", "include_value", "reverse", 0};

	if (!PyArg_ParseTupleAndKeywords(args, kwds, (char*)"|OOO!O!O!O!", (char**)kwargs, &_a, &_b, &PyBool_Type, &verify_checksums, &PyBool_Type, &fill_cache, &PyBool_Type, &include_value, &PyBool_Type, &is_reverse))
		return 0;

	std::string from;
	std::string to;

	leveldb::ReadOptions read_options;
	read_options.verify_checksums = (verify_checksums == Py_True) ? true : false;
	read_options.fill_cache = (fill_cache == Py_True) ? true : false;
	read_options.snapshot = snapshot;

	if (_a != Py_None) {
		is_from = 1;

		if (!PyArg_Parse(_a, (char*)PARAM_S, PARAM_V(a)))
			return 0;
	}

	if (_b != Py_None) {
		is_to = 1;

		if (!PyArg_Parse(_b, (char*)PARAM_S, PARAM_V(b)))
			return 0;
	}

	if (is_from)
		from = PY_LEVELDB_STRING(a);

	if (is_to)
		to = PY_LEVELDB_STRING(b);

	leveldb::Slice key(is_reverse == Py_True ? to.c_str() : from.c_str(), is_reverse == Py_True ? to.size() : from.size());

	if (is_from)
		PY_LEVELDB_RELEASE_BUFFER(a);

	if (is_to)
		PY_LEVELDB_RELEASE_BUFFER(b);

	// create iterator
	leveldb::Iterator* iter = 0;

	Py_BEGIN_ALLOW_THREADS

	iter = self->_db->NewIterator(read_options);

	// if we have an iterator
	if (iter) {
		// forward iteration
		if (is_reverse == Py_False) {

			if (!is_from)
				iter->SeekToFirst();
			else
				iter->Seek(key);
		} else {

			if (!is_to) {
				iter->SeekToLast();
			} else {
				iter->Seek(key);

				if (!iter->Valid()) {
					iter->SeekToLast();
				} else {
					leveldb::Slice a = key;
					leveldb::Slice b = iter->key();
					int c = self->_options->comparator->Compare(a, b);

					if (c) {
						iter->Prev();
					}
				}
			}
		}
	}

	Py_END_ALLOW_THREADS

	if (iter == 0)
		return PyErr_NoMemory();

	// if iterator is empty, return an empty iterator object
	if (!iter->Valid()) {
		Py_BEGIN_ALLOW_THREADS
		delete iter;
		Py_END_ALLOW_THREADS
		return PyLevelDBIter_New(0, 0, 0, 0, 0, 0);
	}

	// otherwise, we're good
	std::string* s = 0;

	if (is_reverse == Py_False && is_to) {
		s = new std::string(to);

		if (s == 0) {
			Py_BEGIN_ALLOW_THREADS
			delete iter;
			Py_END_ALLOW_THREADS
			return PyErr_NoMemory();
		}
	} else if (is_reverse == Py_True && is_from) {
		s = new std::string(from);

		if (s == 0) {
			Py_BEGIN_ALLOW_THREADS
			delete iter;
			Py_END_ALLOW_THREADS
			return PyErr_NoMemory();
		}
	}

	return PyLevelDBIter_New((PyObject*)self, self, iter, s, (include_value == Py_True) ? 1 : 0, (is_reverse == Py_True) ? 1 : 0);
}

static PyObject* PyLevelDB_RangeIter(PyLevelDB* self, PyObject* args, PyObject* kwds)
{
	return PyLevelDB_RangeIter_(self, 0, args, kwds);
}

static PyObject* PyLevelDBSnapshot_RangeIter(PyLevelDBSnapshot* self, PyObject* args, PyObject* kwds)
{
	return PyLevelDB_RangeIter_(self->db, self->snapshot, args, kwds);
}

static PyObject* PyLevelDB_GetStatus(PyLevelDB* self)
{
	std::string value;

	if (!self->_db->GetProperty(leveldb::Slice("leveldb.stats"), &value)) {
		PyErr_SetString(PyExc_ValueError, "unknown property");
		return 0;
	}

	#if PY_MAJOR_VERSION >= 3	
	return PyUnicode_DecodeLatin1(value.c_str(), value.size(), 0);
	#else
	return PyString_FromString(value.c_str());
	#endif
}

static PyObject* PyLevelDB_CreateSnapshot(PyLevelDB* self)
{
	const leveldb::Snapshot* snapshot = self->_db->GetSnapshot();
	//! TBD: check for GetSnapshot() failures
	return PyLevelDBSnapshot_New(self, snapshot);
}

static PyMethodDef PyLevelDB_methods[] = {
	{(char*)"Put",            (PyCFunction)PyLevelDB_Put,       METH_VARARGS | METH_KEYWORDS, (char*)"add a key/value pair to database, with an optional synchronous disk write" },
	{(char*)"Get",            (PyCFunction)PyLevelDB_Get,       METH_VARARGS | METH_KEYWORDS, (char*)"get a value from the database" },
	{(char*)"Delete",         (PyCFunction)PyLevelDB_Delete,    METH_VARARGS | METH_KEYWORDS, (char*)"delete a value in the database" },
	{(char*)"Write",          (PyCFunction)PyLevelDB_Write,     METH_VARARGS | METH_KEYWORDS, (char*)"apply a write-batch"},
	{(char*)"RangeIter",      (PyCFunction)PyLevelDB_RangeIter, METH_VARARGS | METH_KEYWORDS, (char*)"key/value range scan"},
	{(char*)"GetStats",       (PyCFunction)PyLevelDB_GetStatus, METH_VARARGS | METH_NOARGS,   (char*)"get a mapping of all DB statistics"},
	{(char*)"CreateSnapshot", (PyCFunction)PyLevelDB_CreateSnapshot, METH_NOARGS, (char*)"create a new snapshot from current DB state"},
	{NULL}
};

static PyMethodDef PyWriteBatch_methods[] = {
	{(char*)"Put",    (PyCFunction)PyWriteBatch_Put,    METH_VARARGS, (char*)"add a put op to batch" },
	{(char*)"Delete", (PyCFunction)PyWriteBatch_Delete, METH_VARARGS, (char*)"add a delete op to batch" },
	{NULL}
};

static PyMethodDef PyLevelDBSnapshot_methods[] = {
	{(char*)"Get",       (PyCFunction)PyLevelDBSnaphot_Get,        METH_VARARGS | METH_KEYWORDS, (char*)"get a value from the snapshot" },
	{(char*)"RangeIter", (PyCFunction)PyLevelDBSnapshot_RangeIter, METH_VARARGS | METH_KEYWORDS, (char*)"key/value range scan"},
	{NULL}
};

static int pyleveldb_str_eq(PyObject* p, const char* s)
{
	// 8-bit string
	#if PY_MAJOR_VERSION < 3
	if (PyString_Check(p) && strcmp(PyString_AS_STRING(p), "bytewise") == 0)
		return 1;
	#endif

	// unicode string
	if (PyUnicode_Check(p)) {
		size_t i = 0;
		Py_UNICODE* c = PyUnicode_AS_UNICODE(p);

		while (s[i] && c[i] && (int)s[i] == (int)c[i])
			i++;

		return ((int)s[i] == (int)c[i]);
	}

	return 0;
}

static const leveldb::Comparator* pyleveldb_get_comparator(PyObject* comparator)
{
	// default comparator
	if (comparator == 0 || pyleveldb_str_eq(comparator, "bytewise"))
		return leveldb::BytewiseComparator();

	// (name-ascii, python-callable)
	const char* cmp_name = 0;
	PyObject* cmp = 0;

	if (!PyArg_Parse(comparator, (char*)"(sO)", &cmp_name, &cmp) || !PyCallable_Check(cmp)) {
		PyErr_SetString(PyExc_TypeError, "comparator must be a string, or a 2-tuple (name, func)");
		return 0;
	}

	const leveldb::Comparator* c = new PythonComparatorWrapper(cmp_name, cmp);

	if (c == 0) {
		PyErr_NoMemory();
		return 0;
	}

	return c;
}

static int PyLevelDB_init(PyLevelDB* self, PyObject* args, PyObject* kwds)
{
	// cleanup
	if (self->_db || self->_cache || self->_comparator || self->_options) {
		Py_BEGIN_ALLOW_THREADS

		delete self->_db;
		delete self->_options;
		delete self->_cache;

		if (self->_comparator != leveldb::BytewiseComparator())
			delete self->_comparator;

		Py_END_ALLOW_THREADS

		self->_db = 0;
		self->_options = 0;
		self->_cache = 0;
		self->_comparator = 0;
	}

	// get params
	const char* db_dir = 0;

	PyObject* create_if_missing = Py_True;
	PyObject* error_if_exists = Py_False;
	PyObject* paranoid_checks = Py_False;
	int block_cache_size = 8 * (2 << 20);
	int write_buffer_size = 4<<20;
	int block_size = 4096;
	int max_open_files = 1000;
	int block_restart_interval = 16;
	const char* kwargs[] = {"filename", "create_if_missing", "error_if_exists", "paranoid_checks", "write_buffer_size", "block_size", "max_open_files", "block_restart_interval", "block_cache_size", "comparator", 0};

	PyObject* comparator = 0;

	if (!PyArg_ParseTupleAndKeywords(args, kwds, (char*)"s|O!O!O!iiiiiO", (char**)kwargs,
		&db_dir,
		&PyBool_Type, &create_if_missing,
		&PyBool_Type, &error_if_exists,
		&PyBool_Type, &paranoid_checks,
		&write_buffer_size,
		&block_size,
		&max_open_files,
		&block_restart_interval,
		&block_cache_size,
		&comparator))
		return -1;

	if (write_buffer_size < 0 || block_size < 0 || max_open_files < 0 || block_restart_interval < 0 || block_cache_size < 0) {
		PyErr_SetString(PyExc_ValueError, "negative write_buffer_size/block_size/max_open_files/block_restart_interval/cache_size");
		return -1;
	}

	// get comparator
	const leveldb::Comparator* c = pyleveldb_get_comparator(comparator);

	if (c == 0)
		return -1;

	// open database
	self->_options = new leveldb::Options();
	self->_cache = leveldb::NewLRUCache(block_cache_size);
	self->_comparator = c;

	if (self->_options == 0 || self->_cache == 0 || self->_comparator == 0) {
		Py_BEGIN_ALLOW_THREADS
		delete self->_options;
		delete self->_cache;

		if (self->_comparator != leveldb::BytewiseComparator())
			delete self->_comparator;
		Py_END_ALLOW_THREADS

		self->_options = 0;
		self->_cache = 0;
		self->_comparator = 0;

		PyErr_NoMemory();
		return -1;
	}

	self->_options->create_if_missing = (create_if_missing == Py_True) ? true : false;
	self->_options->error_if_exists = (error_if_exists == Py_True) ? true : false;
	self->_options->paranoid_checks = (paranoid_checks == Py_True) ? true : false;
	self->_options->write_buffer_size = write_buffer_size;
	self->_options->block_size = block_size;
	self->_options->max_open_files = max_open_files;
	self->_options->block_restart_interval = block_restart_interval;
	self->_options->compression = leveldb::kSnappyCompression;
	self->_options->block_cache = self->_cache;
	self->_options->comparator = self->_comparator;
	leveldb::Status status;

	// note: copy string parameter, since we might lose it when we release the GIL
	std::string _db_dir(db_dir);

	int i = 0;

	Py_BEGIN_ALLOW_THREADS
	status = leveldb::DB::Open(*self->_options, _db_dir, &self->_db);

	if (!status.ok()) {
		delete self->_db;
		delete self->_options;
		delete self->_cache;

		//! move out of thread block
		if (self->_comparator != leveldb::BytewiseComparator())
			delete self->_comparator;

		self->_db = 0;
		self->_options = 0;
		self->_cache = 0;
		self->_comparator = 0;

		i = -1;
	}

	Py_END_ALLOW_THREADS

	if (i == -1)
		PyLevelDB_set_error(status);

	return i;
}

static int PyWriteBatch_init(PyWriteBatch* self, PyObject* args, PyObject* kwds)
{
	self->ops->clear();
	static char* kwargs[] = {0};

	if (!PyArg_ParseTupleAndKeywords(args, kwds, (char*)"", kwargs))
		return -1;

	return 0;
}

static int PyLevelDBSnapshot_init(PyLevelDBSnapshot* self, PyObject* args, PyObject* kwds)
{
	if (self->db && self->snapshot) {
		self->db->n_snapshots -= 1;
		self->db->_db->ReleaseSnapshot(self->snapshot);
		Py_DECREF(self->db);
	}

	self->db = 0;
	self->snapshot = 0;
	PyLevelDB* db = 0;
	const leveldb::Snapshot* snapshot;
	const char* kwargs[] = {"db", 0};

	if (!PyArg_ParseTupleAndKeywords(args, kwds, (char*)"O!", (char**)kwargs, &PyLevelDB_Type, &db))
		return -1;

	snapshot = db->_db->GetSnapshot();

	//! TBD: deal with GetSnapshot() failure

	self->db = db;
	self->snapshot = snapshot;

	Py_INCREF(self->db);
	self->db->n_snapshots += 1;

	return 0;
}

static int PyLevelDBSnapshot_traverse(PyLevelDBSnapshot* iter, visitproc visit, void* arg)
{
	Py_VISIT((PyObject*)iter->db);
	return 0;
}

PyDoc_STRVAR(PyLevelDB_doc,
"LevelDB(filename, **kwargs) -> leveldb object\n"
"\n"
"Open a LevelDB database, from the given directory.\n"
"\n"
"Only the parameter filename is mandatory.\n"
"\n"
"filename                                    the database directory\n"
"create_if_missing (default: True)           if True, creates a new database if none exists\n"
"error_if_exists   (default: False)          if True, raises and error if the database already exists\n"
"paranoid_checks   (default: False)          if True, raises an error as soon as an internal corruption is detected\n" 
"block_cache_size  (default: 8 * (2 << 20))  maximum allowed size for the block cache in bytes\n"
"write_buffer_size (default  2 * (2 << 20))  \n"
"block_size        (default: 4096)           unit of transfer for the block cache in bytes\n"
"max_open_files:   (default: 1000)\n"
"block_restart_interval           \n"
"\n"
"Snappy compression is used, if available.\n"
"\n"
"Some methods support the following parameters, having these semantics:\n"
"\n"
" verify_checksum: iff True, the operation will check for checksum mismatches\n"
" fill_cache:      iff True, the operation will fill the cache with the data read\n"
" sync:            iff True, the operation will be guaranteed to sync the operation to disk\n"
"\n"
"Methods supported are:\n"
"\n"
" Get(key, verify_checksums = False, fill_cache = True): get value, raises KeyError if key not found\n"
"\n"
"    key: the query key\n"
"\n"
" Put(key, value, sync = False): put key/value pair\n"
"\n"
"    key: the key\n"
"    value: the value\n"
"\n"
" Delete(key, sync = False): delete key/value pair, raises no error kf key not found\n"
"\n"
"    key: the key\n"
"\n"
" Write(write_batch, sync = False): apply multiple put/delete operations atomatically\n"
"\n"
"    write_batch: the WriteBatch object holding the operations\n"
"\n"
" RangeIter(key_from = None, key_to = None, include_value = True, verify_checksums = False, fill_cache = True): return iterator\n"
"\n"
"    key_from: if not None: defines lower bound (inclusive) for iterator\n"
"    key_to:   if not None: defined upper bound (inclusive) for iterator\n"
"    include_value: if True, iterator returns key/value 2-tuples, otherwise, just keys\n"
"\n"
" GetStats(): get a string of runtime information\n"
);

PyDoc_STRVAR(PyWriteBatch_doc,
"WriteBatch() -> write batch object\n"
"\n"
"Create an object, which can hold a list of database operations, which\n"
"can be applied atomically.\n"
"\n"
"Methods supported are:\n"
"\n"
" Put(key, value): add put operation to batch\n"
"\n"
"    key: the key\n"
"    value: the value\n"
"\n"
" Delete(key): add delete operation to batch\n"
"\n"
"    key: the key\n"
);

PyDoc_STRVAR(PyLevelDBSnapshot_doc, "");

PyTypeObject PyLevelDB_Type = {
	#if PY_MAJOR_VERSION >= 3
	PyVarObject_HEAD_INIT(NULL, 0)
	#else
	PyObject_HEAD_INIT(NULL)
	0,
	#endif
	(char*)"leveldb.LevelDB",      /*tp_name*/
	sizeof(PyLevelDB),             /*tp_basicsize*/
	0,                             /*tp_itemsize*/
	(destructor)PyLevelDB_dealloc, /*tp_dealloc*/
	0,                             /*tp_print*/
	0,                             /*tp_getattr*/
	0,                             /*tp_setattr*/
	0,                             /*tp_compare*/
	0,                             /*tp_repr*/
	0,                             /*tp_as_number*/
	0,                             /*tp_as_sequence*/
	0,                             /*tp_as_mapping*/
	0,                             /*tp_hash */
	0,                             /*tp_call*/
	0,                             /*tp_str*/
	0,                             /*tp_getattro*/
	0,                             /*tp_setattro*/
	0,                             /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT,            /*tp_flags*/
	(char*)PyLevelDB_doc,          /*tp_doc */
	0,                             /*tp_traverse */
	0,                             /*tp_clear */
	0,                             /*tp_richcompare */
	0,                             /*tp_weaklistoffset */
	0,                             /*tp_iter */
	0,                             /*tp_iternext */
	PyLevelDB_methods,             /*tp_methods */
	0,                             /*tp_members */
	0,                             /*tp_getset */
	0,                             /*tp_base */
	0,                             /*tp_dict */
	0,                             /*tp_descr_get */
	0,                             /*tp_descr_set */
	0,                             /*tp_dictoffset */
	(initproc)PyLevelDB_init,      /*tp_init */
	0,                             /*tp_alloc */
	PyLevelDB_new,                 /*tp_new */
};


PyTypeObject PyWriteBatch_Type = {
	#if PY_MAJOR_VERSION >= 3
	PyVarObject_HEAD_INIT(NULL, 0)
	#else
	PyObject_HEAD_INIT(NULL)
	0,
	#endif
	(char*)"leveldb.WriteBatch",      /*tp_name*/
	sizeof(PyWriteBatch),             /*tp_basicsize*/
	0,                                /*tp_itemsize*/
	(destructor)PyWriteBatch_dealloc, /*tp_dealloc*/
	0,                                /*tp_print*/
	0,                                /*tp_getattr*/
	0,                                /*tp_setattr*/
	0,                                /*tp_compare*/
	0,                                /*tp_repr*/
	0,                                /*tp_as_number*/
	0,                                /*tp_as_sequence*/
	0,                                /*tp_as_mapping*/
	0,                                /*tp_hash */
	0,                                /*tp_call*/
	0,                                /*tp_str*/
	0,                                /*tp_getattro*/
	0,                                /*tp_setattro*/
	0,                                /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT,               /*tp_flags*/
	(char*)PyWriteBatch_doc,          /*tp_doc */
	0,                                /*tp_traverse */
	0,                                /*tp_clear */
	0,                                /*tp_richcompare */
	0,                                /*tp_weaklistoffset */
	0,                                /*tp_iter */
	0,                                /*tp_iternext */
	PyWriteBatch_methods,             /*tp_methods */
	0,                                /*tp_members */
	0,                                /*tp_getset */
	0,                                /*tp_base */
	0,                                /*tp_dict */
	0,                                /*tp_descr_get */
	0,                                /*tp_descr_set */
	0,                                /*tp_dictoffset */
	(initproc)PyWriteBatch_init,      /*tp_init */
	0,                                /*tp_alloc */
	PyWriteBatch_new,                 /*tp_new */
};

PyTypeObject PyLevelDBSnapshot_Type = {
	#if PY_MAJOR_VERSION >= 3
	PyVarObject_HEAD_INIT(NULL, 0)
	#else
	PyObject_HEAD_INIT(NULL)
	0,
	#endif
	(char*)"leveldb.Snapshot",      /*tp_name*/
	sizeof(PyLevelDBSnapshot),             /*tp_basicsize*/
	0,                                /*tp_itemsize*/
	(destructor)PyLevelDBSnapshot_dealloc, /*tp_dealloc*/
	0,                                /*tp_print*/
	0,                                /*tp_getattr*/
	0,                                /*tp_setattr*/
	0,                                /*tp_compare*/
	0,                                /*tp_repr*/
	0,                                /*tp_as_number*/
	0,                                /*tp_as_sequence*/
	0,                                /*tp_as_mapping*/
	0,                                /*tp_hash */
	0,                                /*tp_call*/
	0,                                /*tp_str*/
	PyObject_GenericGetAttr,         /* tp_getattro */
	0,                               /* tp_setattro */
	0,                               /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT  | Py_TPFLAGS_HAVE_GC, /* tp_flags */
	(char*)PyLevelDBSnapshot_doc,          /*tp_doc */
	(traverseproc)PyLevelDBSnapshot_traverse,  /* tp_traverse */
	0,                                /*tp_clear */
	0,                                /*tp_richcompare */
	0,                                /*tp_weaklistoffset */
	0,                                /*tp_iter */
	0,                                /*tp_iternext */
	PyLevelDBSnapshot_methods,             /*tp_methods */
	0,                                /*tp_members */
	0,                                /*tp_getset */
	0,                                /*tp_base */
	0,                                /*tp_dict */
	0,                                /*tp_descr_get */
	0,                                /*tp_descr_set */
	0,                                /*tp_dictoffset */
	(initproc)PyLevelDBSnapshot_init,      /*tp_init */
	0,                                /*tp_alloc */
	PyLevelDBSnapshot_new,                 /*tp_new */
};

static void PyLevelDBIter_clean(PyLevelDBIter* iter)
{
	if (iter->db)
		iter->db->n_iterators -= 1;

	Py_BEGIN_ALLOW_THREADS

	delete iter->iterator;
	delete iter->bound;

	Py_END_ALLOW_THREADS

	Py_XDECREF(iter->ref);

	iter->ref = 0;
	iter->db = 0;
	iter->iterator = 0;
	iter->bound = 0;
	iter->include_value = 0;
}

static void PyLevelDBIter_dealloc(PyLevelDBIter* iter)
{
	PyLevelDBIter_clean(iter);
	PyObject_GC_Del(iter);
}

static int PyLevelDBIter_traverse(PyLevelDBIter* iter, visitproc visit, void* arg)
{
	Py_VISIT((PyObject*)iter->ref);
	return 0;
}

static PyObject* PyLevelDBIter_next(PyLevelDBIter* iter)
{
	// empty, do cleanup (idempotent)
	if (iter->ref == 0 || !iter->iterator->Valid()) {
		PyLevelDBIter_clean(iter);
		return 0;
	}

	// if we have an upper/lower bound, and we have run past it, clean up and return
	if (iter->bound) {
		leveldb::Slice a = leveldb::Slice(iter->bound->c_str(), iter->bound->size());
		leveldb::Slice b = iter->iterator->key();
		int c = iter->db->_options->comparator->Compare(a, b);

		if (!iter->is_reverse && !(0 <= c)) {
			PyLevelDBIter_clean(iter);
			return 0;
		} else if (iter->is_reverse && !(0 >= c)) {
			PyLevelDBIter_clean(iter);
			return 0;
		}
	}

	// get key and (optional) value
	PyObject* key = PY_LEVELDB_STRING_OR_BYTEARRAY(iter->iterator->key().data(), iter->iterator->key().size());

	PyObject* value = 0;
	PyObject* ret = key;

	if (key == 0)
		return 0;

	if (iter->include_value) {
		value = PY_LEVELDB_STRING_OR_BYTEARRAY(iter->iterator->value().data(), iter->iterator->value().size());

		if (value == 0) {
			Py_XDECREF(key);
			return 0;
		}
	}

	// key/value pairs are returned as 2-tuples
	if (value) {
		ret = PyTuple_New(2);

		if (ret == 0) {
			Py_DECREF(key);
			Py_XDECREF(value);
			return 0;
		}

		PyTuple_SET_ITEM(ret, 0, key);
		PyTuple_SET_ITEM(ret, 1, value);
	}

	// get next/prev value
	if (iter->is_reverse) {
		iter->iterator->Prev();
	} else {
		iter->iterator->Next();
	}
	// return k/v pair or single key
	return ret;
}

PyTypeObject PyLevelDBIter_Type = {
	#if PY_MAJOR_VERSION >= 3
	PyVarObject_HEAD_INIT(NULL, 0)
	#else
	PyObject_HEAD_INIT(NULL)
	0,
	#endif
	(char*)"leveldb-iterator",       /* tp_name */
	sizeof(PyLevelDBIter),             /* tp_basicsize */
	0,                               /* tp_itemsize */
	(destructor)PyLevelDBIter_dealloc, /* tp_dealloc */
	0,                               /* tp_print */
	0,                               /* tp_getattr */
	0,                               /* tp_setattr */
	0,                               /* tp_compare */
	0,                               /* tp_repr */
	0,                               /* tp_as_number */
	0,                               /* tp_as_sequence */
	0,                               /* tp_as_mapping */
	0,                               /* tp_hash */
	0,                               /* tp_call */
	0,                               /* tp_str */
	PyObject_GenericGetAttr,         /* tp_getattro */
	0,                               /* tp_setattro */
	0,                               /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT  | Py_TPFLAGS_HAVE_GC, /* tp_flags */
	0,                               /* tp_doc */
	(traverseproc)PyLevelDBIter_traverse,  /* tp_traverse */
	0,                               /* tp_clear */
	0,                               /* tp_richcompare */
	0,                               /* tp_weaklistoffset */
	PyObject_SelfIter,               /* tp_iter */
	(iternextfunc)PyLevelDBIter_next,  /* tp_iternext */
	0,                               /* tp_methods */
	0,
};

static PyObject* PyLevelDBIter_New(PyObject* ref, PyLevelDB* db, leveldb::Iterator* iterator, std::string* bound, int include_value, int is_reverse)
{
	PyLevelDBIter* iter = PyObject_GC_New(PyLevelDBIter, &PyLevelDBIter_Type);

	if (iter == 0) {
		Py_BEGIN_ALLOW_THREADS
		delete iterator;
		Py_END_ALLOW_THREADS
		return 0;
	}

	Py_XINCREF(ref);
	iter->ref = ref;
	iter->db = db;
	iter->iterator = iterator;
	iter->is_reverse = is_reverse;
	iter->bound = bound;
	iter->include_value = include_value;

	if (iter->db)
		iter->db->n_iterators += 1;

	PyObject_GC_Track(iter);
	return (PyObject*)iter;
}

static PyObject* PyLevelDBSnapshot_New(PyLevelDB* db, const leveldb::Snapshot* snapshot)
{
	PyLevelDBSnapshot* s = PyObject_GC_New(PyLevelDBSnapshot, &PyLevelDBSnapshot_Type);

	if (s == 0) {
		db->_db->ReleaseSnapshot(snapshot);
		return 0;
	}

	Py_INCREF(db);
	s->db = db;
	s->snapshot = snapshot;
	s->db->n_snapshots += 1;
	PyObject_GC_Track(s);
	return (PyObject*)s;
}
