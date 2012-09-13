/*************************************************************************************************
 * Python binding
 *                                                               Copyright (C) 2009-2010 FAL Labs
 * This file is part of Kyoto Cabinet.
 * This program is free software: you can redistribute it and/or modify it under the terms of
 * the GNU General Public License as published by the Free Software Foundation, either version
 * 3 of the License, or any later version.
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
 * without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 * You should have received a copy of the GNU General Public License along with this program.
 * If not, see <http://www.gnu.org/licenses/>.
 *************************************************************************************************/


#include <kcpolydb.h>

namespace kc = kyotocabinet;

extern "C" {

#undef _POSIX_C_SOURCE
#undef _XOPEN_SOURCE
#include <Python.h>
#include <structmember.h>


/* precedent type declaration */
class SoftString;
class CursorBurrow;
class SoftCursor;
class SoftVisitor;
class SoftFileProcessor;
struct Error_data;
struct Visitor_data;
struct FileProcessor_data;
struct Cursor_data;
struct DB_data;
class NativeFunction;
typedef std::map<std::string, std::string> StringMap;
typedef std::vector<std::string> StringVector;


/* function prototypes */
PyMODINIT_FUNC initkyotocabinet(void);
static bool setconstuint32(PyObject* pyobj, const char* name, uint32_t value);
static void throwruntime(const char* message);
static void throwinvarg();
static PyObject* newstring(const char* str);
static PyObject* newbytes(const char* ptr, size_t size);
static int64_t pyatoi(PyObject* pyobj);
static double pyatof(PyObject* pyobj);
static PyObject* maptopymap(const StringMap* map);
static PyObject* vectortopylist(const StringVector* vec);
static void threadyield();
static bool define_module();
static PyObject* kc_conv_bytes(PyObject* pyself, PyObject* pyargs);
static PyObject* kc_atoi(PyObject* pyself, PyObject* pyargs);
static PyObject* kc_atoix(PyObject* pyself, PyObject* pyargs);
static PyObject* kc_atof(PyObject* pyself, PyObject* pyargs);
static PyObject* kc_hash_murmur(PyObject* pyself, PyObject* pyargs);
static PyObject* kc_hash_fnv(PyObject* pyself, PyObject* pyargs);
static PyObject* kc_levdist(PyObject* pyself, PyObject* pyargs);
static bool define_err();
static bool err_define_child(const char* name, uint32_t code);
static PyObject* err_new(PyTypeObject* pytype, PyObject* pyargs, PyObject* pykwds);
static void err_dealloc(Error_data* data);
static int err_init(Error_data* data, PyObject* pyargs, PyObject* pykwds);
static PyObject* err_repr(Error_data* data);
static PyObject* err_str(Error_data* data);
static PyObject* err_richcmp(Error_data* data, PyObject* right, int op);
static PyObject* err_set(Error_data* data, PyObject* pyargs);
static PyObject* err_code(Error_data* data);
static PyObject* err_name(Error_data* data);
static PyObject* err_message(Error_data* data);
static bool define_vis();
static PyObject* vis_new(PyTypeObject* pytype, PyObject* pyargs, PyObject* pykwds);
static void vis_dealloc(Visitor_data* data);
static int vis_init(Visitor_data* data, PyObject* pyargs, PyObject* pykwds);
static PyObject* vis_visit_full(Visitor_data* data, PyObject* pyargs);
static PyObject* vis_visit_empty(Visitor_data* data, PyObject* pyargs);
static bool define_fproc();
static PyObject* fproc_new(PyTypeObject* pytype, PyObject* pyargs, PyObject* pykwds);
static void fproc_dealloc(FileProcessor_data* data);
static int fproc_init(FileProcessor_data* data, PyObject* pyargs, PyObject* pykwds);
static PyObject* fproc_process(FileProcessor_data* data, PyObject* pyargs);
static bool define_cur();
static PyObject* cur_new(PyTypeObject* pytype, PyObject* pyargs, PyObject* pykwds);
static void cur_dealloc(Cursor_data* data);
static int cur_init(Cursor_data* data, PyObject* pyargs, PyObject* pykwds);
static PyObject* cur_repr(Cursor_data* data);
static PyObject* cur_str(Cursor_data* data);
static PyObject* cur_disable(Cursor_data* data);
static PyObject* cur_accept(Cursor_data* data, PyObject* pyargs);
static PyObject* cur_set_value(Cursor_data* data, PyObject* pyargs);
static PyObject* cur_remove(Cursor_data* data);
static PyObject* cur_get_key(Cursor_data* data, PyObject* pyargs);
static PyObject* cur_get_key_str(Cursor_data* data, PyObject* pyargs);
static PyObject* cur_get_value(Cursor_data* data, PyObject* pyargs);
static PyObject* cur_get_value_str(Cursor_data* data, PyObject* pyargs);
static PyObject* cur_get(Cursor_data* data, PyObject* pyargs);
static PyObject* cur_get_str(Cursor_data* data, PyObject* pyargs);
static PyObject* cur_seize(Cursor_data* data);
static PyObject* cur_seize_str(Cursor_data* data);
static PyObject* cur_jump(Cursor_data* data, PyObject* pyargs);
static PyObject* cur_jump_back(Cursor_data* data, PyObject* pyargs);
static PyObject* cur_step(Cursor_data* data);
static PyObject* cur_step_back(Cursor_data* data);
static PyObject* cur_db(Cursor_data* data);
static PyObject* cur_error(Cursor_data* data);
static PyObject* cur_op_iter(Cursor_data* data);
static PyObject* cur_op_iternext(Cursor_data* data);
static bool define_db();
static PyObject* db_new(PyTypeObject* pytype, PyObject* pyargs, PyObject* pykwds);
static void db_dealloc(DB_data* data);
static bool db_raise(DB_data* data);
static int db_init(DB_data* data, PyObject* pyargs, PyObject* pykwds);
static PyObject* db_repr(DB_data* data);
static PyObject* db_str(DB_data* data);
static PyObject* db_error(DB_data* data);
static PyObject* db_open(DB_data* data, PyObject* pyargs);
static PyObject* db_close(DB_data* data);
static PyObject* db_accept(DB_data* data, PyObject* pyargs);
static PyObject* db_accept_bulk(DB_data* data, PyObject* pyargs);
static PyObject* db_iterate(DB_data* data, PyObject* pyargs);
static PyObject* db_set(DB_data* data, PyObject* pyargs);
static PyObject* db_add(DB_data* data, PyObject* pyargs);
static PyObject* db_replace(DB_data* data, PyObject* pyargs);
static PyObject* db_append(DB_data* data, PyObject* pyargs);
static PyObject* db_increment(DB_data* data, PyObject* pyargs);
static PyObject* db_increment_double(DB_data* data, PyObject* pyargs);
static PyObject* db_cas(DB_data* data, PyObject* pyargs);
static PyObject* db_remove(DB_data* data, PyObject* pyargs);
static PyObject* db_get(DB_data* data, PyObject* pyargs);
static PyObject* db_get_str(DB_data* data, PyObject* pyargs);
static PyObject* db_check(DB_data* data, PyObject* pyargs);
static PyObject* db_seize(DB_data* data, PyObject* pyargs);
static PyObject* db_seize_str(DB_data* data, PyObject* pyargs);
static PyObject* db_set_bulk(DB_data* data, PyObject* pyargs);
static PyObject* db_remove_bulk(DB_data* data, PyObject* pyargs);
static PyObject* db_get_bulk(DB_data* data, PyObject* pyargs);
static PyObject* db_get_bulk_str(DB_data* data, PyObject* pyargs);
static PyObject* db_clear(DB_data* data);
static PyObject* db_synchronize(DB_data* data, PyObject* pyargs);
static PyObject* db_occupy(DB_data* data, PyObject* pyargs);
static PyObject* db_copy(DB_data* data, PyObject* pyargs);
static PyObject* db_begin_transaction(DB_data* data, PyObject* pyargs);
static PyObject* db_end_transaction(DB_data* data, PyObject* pyargs);
static PyObject* db_transaction(DB_data* data, PyObject* pyargs);
static PyObject* db_dump_snapshot(DB_data* data, PyObject* pyargs);
static PyObject* db_load_snapshot(DB_data* data, PyObject* pyargs);
static PyObject* db_count(DB_data* data);
static PyObject* db_size(DB_data* data);
static PyObject* db_path(DB_data* data);
static PyObject* db_status(DB_data* data);
static PyObject* db_match_prefix(DB_data* data, PyObject* pyargs);
static PyObject* db_match_regex(DB_data* data, PyObject* pyargs);
static PyObject* db_match_similar(DB_data* data, PyObject* pyargs);
static PyObject* db_merge(DB_data* data, PyObject* pyargs);
static PyObject* db_cursor(DB_data* data);
static PyObject* db_cursor_process(DB_data* data, PyObject* pyargs);
static PyObject* db_shift(DB_data* data);
static PyObject* db_shift_str(DB_data* data);
static char* db_shift_impl(kc::PolyDB* db, size_t* ksp, const char** vbp, size_t* vsp);
static PyObject* db_tune_exception_rule(DB_data* data, PyObject* pyargs);
static Py_ssize_t db_op_len(DB_data* data);
static PyObject* db_op_getitem(DB_data* data, PyObject* pykey);
static int db_op_setitem(DB_data* data, PyObject* pykey, PyObject* pyvalue);
static PyObject* db_op_iter(DB_data* data);
static PyObject* db_process(PyObject* cls, PyObject* pyargs);


/* global variables */
PyObject* mod_kc;
PyObject* mod_th;
PyObject* mod_time;
PyObject* cls_err;
PyObject* cls_err_children[(int)kc::PolyDB::Error::MISC+1];
PyObject* cls_vis;
PyObject* obj_vis_nop;
PyObject* obj_vis_remove;
PyObject* cls_fproc;
PyObject* cls_cur;
PyObject* cls_db;


/**
 * Generic options.
 */
enum GenericOption {
  GEXCEPTIONAL = 1 << 0,
  GCONCURRENT = 1 << 1
};


/**
 * Wrapper to treat a Python string as a C++ string.
 */
class SoftString {
public:
  explicit SoftString(PyObject* pyobj) :
    pyobj_(pyobj), pystr_(NULL), pybytes_(NULL), ptr_(NULL), size_(0) {
    Py_INCREF(pyobj_);
    if (PyUnicode_Check(pyobj_)) {
      pybytes_ = PyUnicode_AsUTF8String(pyobj_);
      if (pybytes_) {
        ptr_ = PyBytes_AS_STRING(pybytes_);
        size_ = PyBytes_GET_SIZE(pybytes_);
      } else {
        PyErr_Clear();
        ptr_ = "";
        size_ = 0;
      }
    } else if (PyBytes_Check(pyobj_)) {
      ptr_ = PyBytes_AS_STRING(pyobj_);
      size_ = PyBytes_GET_SIZE(pyobj_);
    } else if (PyByteArray_Check(pyobj_)) {
      ptr_ = PyByteArray_AS_STRING(pyobj_);
      size_ = PyByteArray_GET_SIZE(pyobj_);
    } else if (pyobj_ == Py_None) {
      ptr_ = "";
      size_ = 0;
    } else {
      pystr_ = PyObject_Str(pyobj_);
      if (pystr_) {
        if (PyBytes_Check(pystr_)) {
          ptr_ = PyBytes_AS_STRING(pystr_);
          size_ = PyBytes_GET_SIZE(pystr_);
        } else {
          pybytes_ = PyUnicode_AsUTF8String(pystr_);
          if (pybytes_) {
            ptr_ = PyBytes_AS_STRING(pybytes_);
            size_ = PyBytes_GET_SIZE(pybytes_);
          } else {
            PyErr_Clear();
            ptr_ = "";
            size_ = 0;
          }
        }
      } else {
        ptr_ = "(unknown)";
        size_ = std::strlen(ptr_);
      }
    }
  }
  ~SoftString() {
    if (pybytes_) Py_DECREF(pybytes_);
    if (pystr_) Py_DECREF(pystr_);
    Py_DECREF(pyobj_);
  }
  const char* ptr() {
    return ptr_;
  }
  const size_t size() {
    return size_;
  }
private:
  PyObject* pyobj_;
  PyObject* pystr_;
  PyObject* pybytes_;
  const char* ptr_;
  size_t size_;
};


/**
 * Burrow of cursors no longer in use.
 */
class CursorBurrow {
private:
  typedef std::vector<kc::PolyDB::Cursor*> CursorList;
public:
  explicit CursorBurrow() : dcurs_() {}
  ~CursorBurrow() {
    sweap();
  }
  void sweap() {
    if (dcurs_.size() > 0) {
      CursorList::iterator dit = dcurs_.begin();
      CursorList::iterator ditend = dcurs_.end();
      while (dit != ditend) {
        kc::PolyDB::Cursor* cur = *dit;
        delete cur;
        dit++;
      }
      dcurs_.clear();
    }
  }
  void deposit(kc::PolyDB::Cursor* cur) {
    dcurs_.push_back(cur);
  }
private:
  CursorList dcurs_;
} g_curbur;


/**
 * Wrapper of a cursor.
 */
class SoftCursor {
public:
  explicit SoftCursor(kc::PolyDB* db) : cur_(NULL) {
    cur_ = db->cursor();
  }
  ~SoftCursor() {
    if (cur_) g_curbur.deposit(cur_);
  }
  kc::PolyDB::Cursor* cur() {
    return cur_;
  }
  void disable() {
    delete cur_;
    cur_ = NULL;
  }
private:
  kc::PolyDB::Cursor* cur_;
};


/**
 * Wrapper of a visitor.
 */
class SoftVisitor : public kc::PolyDB::Visitor {
public:
  explicit SoftVisitor(PyObject* pyvisitor, bool writable) :
    pyvisitor_(pyvisitor), writable_(writable), pyrv_(NULL), rv_(NULL),
    pyextype_(NULL), pyexvalue_(NULL), pyextrace_(NULL) {
    Py_INCREF(pyvisitor_);
  }
  ~SoftVisitor() {
    cleanup();
    Py_DECREF(pyvisitor_);
  }
  bool exception(PyObject** typep, PyObject** valuep, PyObject** tracep) {
    if (!pyextype_) return false;
    *typep = pyextype_;
    *valuep = pyexvalue_;
    *tracep = pyextrace_;
    return true;
  }
private:
  const char* visit_full(const char* kbuf, size_t ksiz,
                         const char* vbuf, size_t vsiz, size_t* sp) {
    cleanup();
    PyObject* pyrv;
    if (PyCallable_Check(pyvisitor_)) {
      pyrv = PyObject_CallFunction(pyvisitor_, (char*)"(s#s#)", kbuf, ksiz, vbuf, vsiz);
    } else {
      pyrv = PyObject_CallMethod(pyvisitor_, (char*)"visit_full",
                                 (char*)"(s#s#)", kbuf, ksiz, vbuf, vsiz);
    }
    if (!pyrv) {
      if (PyErr_Occurred()) PyErr_Fetch(&pyextype_, &pyexvalue_, &pyextrace_);
      return NOP;
    }
    if (pyrv == Py_None || pyrv == obj_vis_nop) {
      Py_DECREF(pyrv);
      return NOP;
    }
    if (!writable_) {
      Py_DECREF(pyrv);
      throwruntime("confliction with the read-only parameter");
      if (PyErr_Occurred()) PyErr_Fetch(&pyextype_, &pyexvalue_, &pyextrace_);
      return NOP;
    }
    if (pyrv == obj_vis_remove) {
      Py_DECREF(pyrv);
      return REMOVE;
    }
    pyrv_ = pyrv;
    rv_ = new SoftString(pyrv);
    *sp = rv_->size();
    return rv_->ptr();
  }
  const char* visit_empty(const char* kbuf, size_t ksiz, size_t* sp) {
    cleanup();
    PyObject* pyrv;
    if (PyCallable_Check(pyvisitor_)) {
      pyrv = PyObject_CallFunction(pyvisitor_, (char*)"(s#O)", kbuf, ksiz, Py_None);
    } else {
      pyrv = PyObject_CallMethod(pyvisitor_, (char*)"visit_empty",
                                 (char*)"(s#)", kbuf, ksiz);
    }
    if (!pyrv) {
      if (PyErr_Occurred()) PyErr_Fetch(&pyextype_, &pyexvalue_, &pyextrace_);
      return NOP;
    }
    if (pyrv == Py_None || pyrv == obj_vis_nop) {
      Py_DECREF(pyrv);
      return NOP;
    }
    if (!writable_) {
      Py_DECREF(pyrv);
      throwruntime("confliction with the read-only parameter");
      if (PyErr_Occurred()) PyErr_Fetch(&pyextype_, &pyexvalue_, &pyextrace_);
      return NOP;
    }
    if (pyrv == obj_vis_remove) {
      Py_DECREF(pyrv);
      return REMOVE;
    }
    pyrv_ = pyrv;
    rv_ = new SoftString(pyrv);
    *sp = rv_->size();
    return rv_->ptr();
  }
  void cleanup() {
    if (pyextrace_) {
      Py_DECREF(pyextrace_);
      pyextrace_ = NULL;
    }
    if (pyexvalue_) {
      Py_DECREF(pyexvalue_);
      pyexvalue_ = NULL;
    }
    if (pyextype_) {
      Py_DECREF(pyextype_);
      pyextype_ = NULL;
    }
    delete rv_;
    rv_ = NULL;
    if (pyrv_) {
      Py_DECREF(pyrv_);
      pyrv_ = NULL;
    }
  }
  PyObject* pyvisitor_;
  bool writable_;
  PyObject* pyrv_;
  SoftString* rv_;
  PyObject* pyextype_;
  PyObject* pyexvalue_;
  PyObject* pyextrace_;
};


/**
 * Wrapper of a file processor.
 */
class SoftFileProcessor : public kc::PolyDB::FileProcessor {
public:
  explicit SoftFileProcessor(PyObject* pyproc) :
    pyproc_(pyproc), pyextype_(NULL), pyexvalue_(NULL), pyextrace_(NULL) {
    Py_INCREF(pyproc_);
  }
  ~SoftFileProcessor() {
    if (pyextrace_) Py_DECREF(pyextrace_);
    if (pyexvalue_) Py_DECREF(pyexvalue_);
    if (pyextype_) Py_DECREF(pyextype_);
    Py_DECREF(pyproc_);
  }
  bool exception(PyObject** typep, PyObject** valuep, PyObject** tracep) {
    if (!pyextype_) return false;
    *typep = pyextype_;
    *valuep = pyexvalue_;
    *tracep = pyextrace_;
    return true;
  }
private:
  bool process(const std::string& path, int64_t count, int64_t size) {
    PyObject* pyrv;
    if (PyCallable_Check(pyproc_)) {
      pyrv = PyObject_CallFunction(pyproc_, (char*)"(sLL)",
                                   path.c_str(), (long long)count, (long long)size);
    } else {
      pyrv = PyObject_CallMethod(pyproc_, (char*)"process", (char*)"(sLL)",
                                 path.c_str(), (long long)count, (long long)size);
    }
    if (!pyrv) {
      if (PyErr_Occurred()) PyErr_Fetch(&pyextype_, &pyexvalue_, &pyextrace_);
      return false;
    }
    bool rv = PyObject_IsTrue(pyrv);
    Py_DECREF(pyrv);
    return rv;
  }
  PyObject* pyproc_;
  PyObject* pyextype_;
  PyObject* pyexvalue_;
  PyObject* pyextrace_;
};


/**
 * Internal data of an error object.
 */
struct Error_data {
  PyBaseExceptionObject base;
  PyObject* pycode;
  PyObject* pymessage;
};


/**
 * Internal data of a visitor object.
 */
struct Visitor_data {
  PyObject_HEAD
};


/**
 * Internal data of a file processor object.
 */
struct FileProcessor_data {
  PyObject_HEAD
};


/**
 * Internal data of a cursor object.
 */
struct Cursor_data {
  PyObject_HEAD
  SoftCursor* cur;
  PyObject* pydb;
};


/**
 * Internal data of a database object.
 */
struct DB_data {
  PyObject_HEAD
  kc::PolyDB* db;
  uint32_t exbits;
  PyObject* pylock;
};


/**
 * Locking device of the database.
 */
class NativeFunction {
public:
  NativeFunction(DB_data* data) : data_(data), thstate_(NULL) {
    PyObject* pylock = data_->pylock;
    if (pylock == Py_None) {
      thstate_ = PyEval_SaveThread();
    } else {
      PyObject* pyrv = PyObject_CallMethod(pylock, (char*)"acquire", NULL);
      if (pyrv) Py_DECREF(pyrv);
    }
  }
  void cleanup() {
    PyObject* pylock = data_->pylock;
    if (pylock == Py_None) {
      if (thstate_) PyEval_RestoreThread(thstate_);
    } else {
      PyObject* pyrv = PyObject_CallMethod(pylock, (char*)"release", NULL);
      if (pyrv) Py_DECREF(pyrv);
    }
  }
private:
  DB_data* data_;
  PyThreadState* thstate_;
};


/**
 * Entry point of the library.
 */
PyMODINIT_FUNC initkyotocabinet(void) {
  if (!define_module()) return;
  if (!define_err()) return;
  if (!define_vis()) return;
  if (!define_fproc()) return;
  if (!define_cur()) return;
  if (!define_db()) return;
}


/**
 * Set a constant of unsigned integer.
 */
static bool setconstuint32(PyObject* pyobj, const char* name, uint32_t value) {
  PyObject* pyname = PyString_FromString(name);
  PyObject* pyvalue = PyLong_FromUnsignedLong(value);
  return PyObject_GenericSetAttr(pyobj, pyname, pyvalue) == 0;
}


/**
 * Throw a runtime error.
 */
static void throwruntime(const char* message) {
  PyErr_SetString(PyExc_RuntimeError, message);
}


/**
 * throw the invalid argument error.
 */
static void throwinvarg() {
  PyErr_SetString(PyExc_TypeError, "invalid arguments");
}


/**
 * Create a new string.
 */
static PyObject* newstring(const char* str) {
  return PyUnicode_DecodeUTF8(str, std::strlen(str), "ignore");
}


/**
 * Create a new byte array.
 */
static PyObject* newbytes(const char* ptr, size_t size) {
  return PyBytes_FromStringAndSize(ptr, size);
}


/**
 * Convert a numeric parameter to an integer.
 */
static int64_t pyatoi(PyObject* pyobj) {
  if (PyLong_Check(pyobj)) {
    return PyLong_AsLong(pyobj);
  } else if (PyFloat_Check(pyobj)) {
    double dnum = PyFloat_AsDouble(pyobj);
    if (kc::chknan(dnum)) {
      return kc::INT64MIN;
    } else if (kc::chkinf(dnum)) {
      return dnum < 0 ? kc::INT64MIN : kc::INT64MAX;
    }
    return dnum;
  } else if (PyString_Check(pyobj) || PyUnicode_Check(pyobj) || PyBytes_Check(pyobj)) {
    SoftString numstr(pyobj);
    const char* str = numstr.ptr();
    double dnum = kc::atof(str);
    if (kc::chknan(dnum)) {
      return kc::INT64MIN;
    } else if (kc::chkinf(dnum)) {
      return dnum < 0 ? kc::INT64MIN : kc::INT64MAX;
    }
    return dnum;
  } else if (pyobj != Py_None) {
    int64_t inum = 0;
    PyObject* pylong = PyNumber_Long(pyobj);
    if (pylong) {
      inum = PyLong_AsLong(pyobj);
      Py_DECREF(pylong);
    }
    return inum;
  }
  return 0;
}


/**
 * Convert a numeric parameter to a real number.
 */
static double pyatof(PyObject* pyobj) {
  if (PyLong_Check(pyobj)) {
    return PyLong_AsLong(pyobj);
  } else if (PyFloat_Check(pyobj)) {
    return PyFloat_AsDouble(pyobj);
  } else if (PyString_Check(pyobj) || PyUnicode_Check(pyobj) || PyBytes_Check(pyobj)) {
    SoftString numstr(pyobj);
    const char* str = numstr.ptr();
    return kc::atof(str);
  } else if (pyobj != Py_None) {
    double dnum = 0;
    PyObject* pyfloat = PyNumber_Float(pyobj);
    if (pyfloat) {
      dnum = PyFloat_AsDouble(pyfloat);
      Py_DECREF(pyfloat);
    }
    return dnum;
  }
  return 0;
}


/**
 * Convert an internal map to a Python map.
 */
static PyObject* maptopymap(const StringMap* map) {
  PyObject* pyhash = PyDict_New();
  StringMap::const_iterator it = map->begin();
  StringMap::const_iterator itend = map->end();
  while (it != itend) {
    PyObject* pyvalue = newbytes(it->second.data(), it->second.size());
    PyDict_SetItemString(pyhash, it->first.c_str(), pyvalue);
    Py_DECREF(pyvalue);
    it++;
  }
  return pyhash;
}


/**
 * Convert an internal vector to a Python list.
 */
static PyObject* vectortopylist(const StringVector* vec) {
  size_t num = vec->size();
  PyObject* pylist = PyList_New(num);
  for (size_t i = 0; i < num; i++) {
    PyObject* pystr = newbytes((*vec)[i].data(), (*vec)[i].size());
    PyList_SET_ITEM(pylist, i, pystr);
  }
  return pylist;
}


/**
 * Pass the current execution state.
 */
static void threadyield() {
  PyObject* pyrv = PyObject_CallMethod(mod_time, (char*)"sleep", (char*)"(I)", 0);
  if (pyrv) Py_DECREF(pyrv);
}


/**
 * Define objects of the module.
 */
static bool define_module() {
  static PyMethodDef method_def[] = {
    { "conv_bytes", (PyCFunction)kc_conv_bytes, METH_VARARGS,
      "Convert any object to a byte array." },
    { "atoi", (PyCFunction)kc_atoi, METH_VARARGS,
      "Convert a string to an integer." },
    { "atoix", (PyCFunction)kc_atoix, METH_VARARGS,
      "Convert a string with a metric prefix to an integer." },
    { "atof", (PyCFunction)kc_atof, METH_VARARGS,
      "Convert a string to a real number." },
    { "hash_murmur", (PyCFunction)kc_hash_murmur, METH_VARARGS,
      "Get the hash value of a string by MurMur hashing." },
    { "hash_fnv", (PyCFunction)kc_hash_fnv, METH_VARARGS,
      "Get the hash value of a string by FNV hashing." },
    { "levdist", (PyCFunction)kc_levdist, METH_VARARGS,
      "Calculate the levenshtein distance of two strings." },
    { NULL, NULL, 0, NULL }
  };
  mod_kc = Py_InitModule("kyotocabinet", method_def);
  if (PyModule_AddStringConstant(mod_kc, "VERSION", kc::VERSION) != 0) return false;
  mod_th = PyImport_ImportModule("threading");
  mod_time = PyImport_ImportModule("time");
  if (!mod_th) return false;
  return true;
}


/**
 * Implementation of conv_bytes.
 */
static PyObject* kc_conv_bytes(PyObject* pyself, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pyobj = PyTuple_GetItem(pyargs, 0);
  SoftString str(pyobj);
  return PyBytes_FromStringAndSize(str.ptr(), str.size());
}


/**
 * Implementation of atoi.
 */
static PyObject* kc_atoi(PyObject* pyself, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystr = PyTuple_GetItem(pyargs, 0);
  SoftString str(pystr);
  return PyLong_FromLongLong(kc::atoi(str.ptr()));
}


/**
 * Implementation of atoix.
 */
static PyObject* kc_atoix(PyObject* pyself, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystr = PyTuple_GetItem(pyargs, 0);
  SoftString str(pystr);
  return PyLong_FromLongLong(kc::atoix(str.ptr()));
}


/**
 * Implementation of atof.
 */
static PyObject* kc_atof(PyObject* pyself, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystr = PyTuple_GetItem(pyargs, 0);
  SoftString str(pystr);
  return PyFloat_FromDouble(kc::atof(str.ptr()));
}


/**
 * Implementation of hash_murmur.
 */
static PyObject* kc_hash_murmur(PyObject* pyself, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystr = PyTuple_GetItem(pyargs, 0);
  SoftString str(pystr);
  return PyLong_FromUnsignedLongLong(kc::hashmurmur(str.ptr(), str.size()));
}


/**
 * Implementation of hash_fnv.
 */
static PyObject* kc_hash_fnv(PyObject* pyself, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystr = PyTuple_GetItem(pyargs, 0);
  SoftString str(pystr);
  return PyLong_FromUnsignedLongLong(kc::hashfnv(str.ptr(), str.size()));
}


/**
 * Implementation of levdist.
 */
static PyObject* kc_levdist(PyObject* pyself, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 2) {
    throwinvarg();
    return NULL;
  }
  PyObject* pya = PyTuple_GetItem(pyargs, 0);
  PyObject* pyb = PyTuple_GetItem(pyargs, 1);
  PyObject* pyutf = Py_None;
  if (argc > 2) pyutf = PyTuple_GetItem(pyargs, 2);
  SoftString astr(pya);
  const char* abuf = astr.ptr();
  size_t asiz = astr.size();
  SoftString bstr(pyb);
  const char* bbuf = bstr.ptr();
  size_t bsiz = bstr.size();
  bool utf = PyObject_IsTrue(pyutf);
  size_t dist;
  if (utf) {
    uint32_t astack[128];
    uint32_t* aary = asiz > sizeof(astack) / sizeof(*astack) ? new uint32_t[asiz] : astack;
    size_t anum;
    kc::strutftoucs(abuf, asiz, aary, &anum);
    uint32_t bstack[128];
    uint32_t* bary = bsiz > sizeof(bstack) / sizeof(*bstack) ? new uint32_t[bsiz] : bstack;
    size_t bnum;
    kc::strutftoucs(bbuf, bsiz, bary, &bnum);
    dist = kc::strucsdist(aary, anum, bary, bnum);
    if (bary != bstack) delete[] bary;
    if (aary != astack) delete[] aary;
  } else {
    dist = kc::memdist(abuf, asiz, bbuf, bsiz);
  }
  return PyLong_FromUnsignedLongLong(dist);
}


/**
 * Define objects of the Error class.
 */
static bool define_err() {
  static PyTypeObject type_err = { PyVarObject_HEAD_INIT(NULL, 0) };
  size_t zoff = offsetof(PyTypeObject, tp_name);
  std::memset((char*)&type_err + zoff, 0, sizeof(type_err) - zoff);
  type_err.tp_name = "kyotocabinet.Error";
  type_err.tp_basicsize = sizeof(Error_data);
  type_err.tp_itemsize = 0;
  type_err.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  type_err.tp_doc = "Error data.";
  type_err.tp_new = err_new;
  type_err.tp_dealloc = (destructor)err_dealloc;
  type_err.tp_init = (initproc)err_init;
  type_err.tp_repr = (unaryfunc)err_repr;
  type_err.tp_str = (unaryfunc)err_str;
  type_err.tp_richcompare = (richcmpfunc)err_richcmp;
  static PyMethodDef err_methods[] = {
    { "set", (PyCFunction)err_set, METH_VARARGS,
      "Set the error information." },
    { "code", (PyCFunction)err_code, METH_NOARGS,
      "Get the error code." },
    { "name", (PyCFunction)err_name, METH_NOARGS,
      "Get the readable string of the code." },
    { "message", (PyCFunction)err_message, METH_NOARGS,
      "Get the supplement message." },
    { NULL, NULL, 0, NULL }
  };
  type_err.tp_methods = err_methods;
  type_err.tp_base = (PyTypeObject*)PyExc_RuntimeError;
  if (PyType_Ready(&type_err) != 0) return false;
  cls_err = (PyObject*)&type_err;
  for (size_t i = 0; i < sizeof(cls_err_children) / sizeof(*cls_err_children); i++) {
    cls_err_children[i] = NULL;
  }
  if (!err_define_child("SUCCESS", kc::PolyDB::Error::SUCCESS)) return false;
  if (!err_define_child("NOIMPL", kc::PolyDB::Error::NOIMPL)) return false;
  if (!err_define_child("INVALID", kc::PolyDB::Error::INVALID)) return false;
  if (!err_define_child("NOREPOS", kc::PolyDB::Error::NOREPOS)) return false;
  if (!err_define_child("NOPERM", kc::PolyDB::Error::NOPERM)) return false;
  if (!err_define_child("BROKEN", kc::PolyDB::Error::BROKEN)) return false;
  if (!err_define_child("DUPREC", kc::PolyDB::Error::DUPREC)) return false;
  if (!err_define_child("NOREC", kc::PolyDB::Error::NOREC)) return false;
  if (!err_define_child("LOGIC", kc::PolyDB::Error::LOGIC)) return false;
  if (!err_define_child("SYSTEM", kc::PolyDB::Error::SYSTEM)) return false;
  if (!err_define_child("MISC", kc::PolyDB::Error::MISC)) return false;
  Py_INCREF(cls_err);
  if (PyModule_AddObject(mod_kc, "Error", cls_err) != 0) return false;
  return true;
}


/**
 * Define the constant and the subclass of an error code.
 */
static bool err_define_child(const char* name, uint32_t code) {
  if (!setconstuint32(cls_err, name, code)) return false;
  char xname[kc::NUMBUFSIZ];
  std::sprintf(xname, "X%s", name);
  char fname[kc::NUMBUFSIZ*2];
  std::sprintf(fname, "kyotocabinet.Error.%s", xname);
  PyObject* pyxname = PyUnicode_FromString(xname);
  PyObject* pyvalue = PyErr_NewException(fname, cls_err, NULL);
  cls_err_children[code] = pyvalue;
  return PyObject_GenericSetAttr(cls_err, pyxname, pyvalue) == 0;
}


/**
 * Implementation of new.
 */
static PyObject* err_new(PyTypeObject* pytype, PyObject* pyargs, PyObject* pykwds) {
  Error_data* data = (Error_data*)pytype->tp_alloc(pytype, 0);
  if (!data) return NULL;
  data->pycode = PyLong_FromUnsignedLong(kc::PolyDB::Error::SUCCESS);
  data->pymessage = PyString_FromString("error");
  return (PyObject*)data;
}


/**
 * Implementation of dealloc.
 */
static void err_dealloc(Error_data* data) {
  Py_DECREF(data->pymessage);
  Py_DECREF(data->pycode);
  Py_CLEAR(data->base.dict);
  Py_CLEAR(data->base.args);
  Py_CLEAR(data->base.message);
  Py_TYPE(data)->tp_free((PyObject*)data);
}


/**
 * Implementation of init.
 */
static int err_init(Error_data* data, PyObject* pyargs, PyObject* pykwds) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 2) {
    throwinvarg();
    return -1;
  }
  if (argc > 1) {
    PyObject* pycode = PyTuple_GetItem(pyargs, 0);
    PyObject* pymessage = PyTuple_GetItem(pyargs, 1);
    if (PyLong_Check(pycode) && PyString_Check(pymessage)) {
      Py_DECREF(data->pycode);
      Py_DECREF(data->pymessage);
      Py_INCREF(pycode);
      data->pycode = pycode;
      Py_INCREF(pymessage);
      data->pymessage = pymessage;
    } else if (PyInt_Check(pycode) && PyString_Check(pymessage)) {
      Py_DECREF(data->pycode);
      Py_DECREF(data->pymessage);
      data->pycode = PyLong_FromLong(PyInt_AsLong(pycode));
      Py_INCREF(pymessage);
      data->pymessage = pymessage;
    }
  } else if (argc > 0) {
    PyObject* pyexpr = PyTuple_GetItem(pyargs, 0);
    if (PyString_Check(pyexpr)) {
      const char* expr = PyString_AsString(pyexpr);
      uint32_t code = kc::atoi(expr);
      const char* rp = std::strchr(expr, ':');
      if (rp) expr = rp + 1;
      while (*expr == ' ') {
        expr++;
      }
      Py_DECREF(data->pycode);
      Py_DECREF(data->pymessage);
      data->pycode = PyLong_FromLongLong(code);
      data->pymessage = PyUnicode_FromString(expr);
    }
  }
  return 0;
}


/**
 * Implementation of repr.
 */
static PyObject* err_repr(Error_data* data) {
  uint32_t code = (uint32_t)PyLong_AsLong(data->pycode);
  const char* name = kc::PolyDB::Error::codename((kc::PolyDB::Error::Code)code);
  return PyString_FromFormat("<kyotocabinet.Error: %s: %s>",
                             name, PyString_AsString(data->pymessage));
}


/**
 * Implementation of str.
 */
static PyObject* err_str(Error_data* data) {
  uint32_t code = (uint32_t)PyLong_AsLong(data->pycode);
  const char* name = kc::PolyDB::Error::codename((kc::PolyDB::Error::Code)code);
  return PyString_FromFormat("%s: %s",
                             name, PyString_AsString(data->pymessage));
}


/**
 * Implementation of richcmp.
 */
static PyObject* err_richcmp(Error_data* data, PyObject* pyright, int op) {
  bool rv;
  uint32_t code = (uint32_t)PyLong_AsLong(data->pycode);
  uint32_t rcode;
  if (PyObject_IsInstance(pyright, cls_err)) {
    Error_data* rdata = (Error_data*)pyright;
    rcode = (uint32_t)PyLong_AsLong(rdata->pycode);
  } else if (PyLong_Check(pyright)) {
    rcode = (uint32_t)PyLong_AsLong(pyright);
  } else if (PyInt_Check(pyright)) {
    rcode = (uint32_t)PyInt_AsLong(pyright);
  } else {
    rcode = kc::INT32MAX;
  }
  switch (op) {
    case Py_LT: rv = code < rcode; break;
    case Py_LE: rv = code <= rcode; break;
    case Py_EQ: rv = code == rcode; break;
    case Py_NE: rv = code != rcode; break;
    case Py_GT: rv = code > rcode; break;
    case Py_GE: rv = code >= rcode; break;
    default: rv = false; break;
  }
  if (rv) Py_RETURN_TRUE;
  Py_RETURN_FALSE;
}


/**
 * Implementation of set.
 */
static PyObject* err_set(Error_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 2) {
    throwinvarg();
    return NULL;
  }
  PyObject* pycode = PyTuple_GetItem(pyargs, 0);
  PyObject* pymessage = PyTuple_GetItem(pyargs, 1);
  if (PyLong_Check(pycode) && PyString_Check(pymessage)) {
    Py_DECREF(data->pycode);
    Py_DECREF(data->pymessage);
    Py_INCREF(pycode);
    data->pycode = pycode;
    Py_INCREF(pymessage);
    data->pymessage = pymessage;
  } else if (PyInt_Check(pycode) && PyString_Check(pymessage)) {
    Py_DECREF(data->pycode);
    Py_DECREF(data->pymessage);
    data->pycode = PyLong_FromLong(PyInt_AsLong(pycode));
    Py_INCREF(pymessage);
    data->pymessage = pymessage;
  } else {
    throwinvarg();
    return NULL;
  }
  Py_RETURN_NONE;
}


/**
 * Implementation of code.
 */
static PyObject* err_code(Error_data* data) {
  Py_INCREF(data->pycode);
  return data->pycode;
}


/**
 * Implementation of name.
 */
static PyObject* err_name(Error_data* data) {
  uint32_t code = PyLong_AsLong(data->pycode);
  const char* name = kc::PolyDB::Error::codename((kc::PolyDB::Error::Code)code);
  return PyString_FromString(name);
}


/**
 * Implementation of message.
 */
static PyObject* err_message(Error_data* data) {
  Py_INCREF(data->pymessage);
  return data->pymessage;
}


/**
 * Define objects of the Visitor class.
 */
static bool define_vis() {
  static PyTypeObject type_vis = { PyVarObject_HEAD_INIT(NULL, 0) };
  size_t zoff = offsetof(PyTypeObject, tp_name);
  std::memset((char*)&type_vis + zoff, 0, sizeof(type_vis) - zoff);
  type_vis.tp_name = "kyotocabinet.Visitor";
  type_vis.tp_basicsize = sizeof(Visitor_data);
  type_vis.tp_itemsize = 0;
  type_vis.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  type_vis.tp_doc = "Interface to access a record.";
  type_vis.tp_new = vis_new;
  type_vis.tp_dealloc = (destructor)vis_dealloc;
  type_vis.tp_init = (initproc)vis_init;
  static PyMethodDef vis_methods[] = {
    { "visit_full", (PyCFunction)vis_visit_full, METH_VARARGS,
      "Visit a record.", },
    { "visit_empty", (PyCFunction)vis_visit_empty, METH_VARARGS,
      "Visit a empty record space." },
    { NULL, NULL, 0, NULL }
  };
  type_vis.tp_methods = vis_methods;
  if (PyType_Ready(&type_vis) != 0) return false;
  cls_vis = (PyObject*)&type_vis;
  PyObject* pyname = PyString_FromString("NOP");
  obj_vis_nop = PyString_FromString("[NOP]");
  if (PyObject_GenericSetAttr(cls_vis, pyname, obj_vis_nop) != 0) return false;
  pyname = PyString_FromString("REMOVE");
  obj_vis_remove = PyString_FromString("[REMOVE]");
  if (PyObject_GenericSetAttr(cls_vis, pyname, obj_vis_remove) != 0) return false;
  Py_INCREF(cls_vis);
  if (PyModule_AddObject(mod_kc, "Visitor", cls_vis) != 0) return false;
  return true;
}


/**
 * Implementation of new.
 */
static PyObject* vis_new(PyTypeObject* pytype, PyObject* pyargs, PyObject* pykwds) {
  Visitor_data* data = (Visitor_data*)pytype->tp_alloc(pytype, 0);
  if (!data) return NULL;
  return (PyObject*)data;
}


/**
 * Implementation of dealloc.
 */
static void vis_dealloc(Visitor_data* data) {
  Py_TYPE(data)->tp_free((PyObject*)data);
}


/**
 * Implementation of init.
 */
static int vis_init(Visitor_data* data, PyObject* pyargs, PyObject* pykwds) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 0) {
    throwinvarg();
    return -1;
  }
  return 0;
}


/**
 * Implementation of visit_full.
 */
static PyObject* vis_visit_full(Visitor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 2) {
    throwinvarg();
    return NULL;
  }
  Py_INCREF(obj_vis_nop);
  return obj_vis_nop;
}


/**
 * Implementation of visit_empty.
 */
static PyObject* vis_visit_empty(Visitor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  Py_INCREF(obj_vis_nop);
  return obj_vis_nop;
}


/**
 * Define objects of the FileProcessor class.
 */
static bool define_fproc() {
  static PyTypeObject type_fproc = { PyVarObject_HEAD_INIT(NULL, 0) };
  size_t zoff = offsetof(PyTypeObject, tp_name);
  std::memset((char*)&type_fproc + zoff, 0, sizeof(type_fproc) - zoff);
  type_fproc.tp_name = "kyotocabinet.FileProcessor";
  type_fproc.tp_basicsize = sizeof(FileProcessor_data);
  type_fproc.tp_itemsize = 0;
  type_fproc.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  type_fproc.tp_doc = "Interface to process the database file.";
  type_fproc.tp_new = fproc_new;
  type_fproc.tp_dealloc = (destructor)fproc_dealloc;
  type_fproc.tp_init = (initproc)fproc_init;
  static PyMethodDef fproc_methods[] = {
    { "process", (PyCFunction)fproc_process, METH_VARARGS,
      "Process the database file.", },
    { NULL, NULL, 0, NULL }
  };
  type_fproc.tp_methods = fproc_methods;
  if (PyType_Ready(&type_fproc) != 0) return false;
  cls_fproc = (PyObject*)&type_fproc;
  Py_INCREF(cls_fproc);
  if (PyModule_AddObject(mod_kc, "FileProcessor", cls_fproc) != 0) return false;
  return true;
}


/**
 * Implementation of new.
 */
static PyObject* fproc_new(PyTypeObject* pytype, PyObject* pyargs, PyObject* pykwds) {
  FileProcessor_data* data = (FileProcessor_data*)pytype->tp_alloc(pytype, 0);
  if (!data) return NULL;
  return (PyObject*)data;
}


/**
 * Implementation of dealloc.
 */
static void fproc_dealloc(FileProcessor_data* data) {
  Py_TYPE(data)->tp_free((PyObject*)data);
}


/**
 * Implementation of init.
 */
static int fproc_init(FileProcessor_data* data, PyObject* pyargs, PyObject* pykwds) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 0) {
    throwinvarg();
    return -1;
  }
  return 0;
}


/**
 * Implementation of process.
 */
static PyObject* fproc_process(FileProcessor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 3) {
    throwinvarg();
    return NULL;
  }
  Py_RETURN_TRUE;
}


/**
 * Define objects of the Cursor class.
 */
static bool define_cur() {
  static PyTypeObject type_cur = { PyVarObject_HEAD_INIT(NULL, 0) };
  size_t zoff = offsetof(PyTypeObject, tp_name);
  std::memset((char*)&type_cur + zoff, 0, sizeof(type_cur) - zoff);
  type_cur.tp_name = "kyotocabinet.Cursor";
  type_cur.tp_basicsize = sizeof(Cursor_data);
  type_cur.tp_itemsize = 0;
  type_cur.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  type_cur.tp_doc = "Interface of cursor to indicate a record.";
  type_cur.tp_new = cur_new;
  type_cur.tp_dealloc = (destructor)cur_dealloc;
  type_cur.tp_init = (initproc)cur_init;
  type_cur.tp_repr = (unaryfunc)cur_repr;
  type_cur.tp_str = (unaryfunc)cur_str;
  static PyMethodDef cur_methods[] = {
    { "disable", (PyCFunction)cur_disable, METH_NOARGS,
      "Disable the cursor." },
    { "accept", (PyCFunction)cur_accept, METH_VARARGS,
      "Accept a visitor to the current record." },
    { "set_value", (PyCFunction)cur_set_value, METH_VARARGS,
      "Set the value of the current record." },
    { "remove", (PyCFunction)cur_remove, METH_NOARGS,
      "Remove the current record." },
    { "get_key", (PyCFunction)cur_get_key, METH_VARARGS,
      "Get the key of the current record." },
    { "get_key_str", (PyCFunction)cur_get_key_str, METH_VARARGS,
      "Get the key of the current record." },
    { "get_value", (PyCFunction)cur_get_value, METH_VARARGS,
      "Get the value of the current record." },
    { "get_value_str", (PyCFunction)cur_get_value_str, METH_VARARGS,
      "Get the value of the current record." },
    { "get", (PyCFunction)cur_get, METH_VARARGS,
      "Get a pair of the key and the value of the current record." },
    { "get_str", (PyCFunction)cur_get_str, METH_VARARGS,
      "Get a pair of the key and the value of the current record." },
    { "seize", (PyCFunction)cur_seize, METH_NOARGS,
      "Get a pair of the key and the value of the current record and remove it atomically." },
    { "seize_str", (PyCFunction)cur_seize_str, METH_NOARGS,
      "Get a pair of the key and the value of the current record and remove it atomically." },
    { "jump", (PyCFunction)cur_jump, METH_VARARGS,
      "Jump the cursor to a record for forward scan." },
    { "jump_back", (PyCFunction)cur_jump_back, METH_VARARGS,
      "Jump the cursor to a record for backward scan." },
    { "step", (PyCFunction)cur_step, METH_NOARGS,
      "Step the cursor to the next record." },
    { "step_back", (PyCFunction)cur_step_back, METH_NOARGS,
      "Step the cursor to the previous record." },
    { "db", (PyCFunction)cur_db, METH_NOARGS,
      "Get the database object." },
    { "error", (PyCFunction)cur_error, METH_NOARGS,
      "Get the last happened error." },
    { NULL, NULL, 0, NULL }
  };
  type_cur.tp_methods = cur_methods;
  type_cur.tp_iter = (getiterfunc)cur_op_iter;
  type_cur.tp_iternext = (iternextfunc)cur_op_iternext;
  if (PyType_Ready(&type_cur) != 0) return false;
  cls_cur = (PyObject*)&type_cur;
  Py_INCREF(cls_cur);
  if (PyModule_AddObject(mod_kc, "Cursor", cls_cur) != 0) return false;
  return true;
}


/**
 * Implementation of new.
 */
static PyObject* cur_new(PyTypeObject* pytype, PyObject* pyargs, PyObject* pykwds) {
  Cursor_data* data = (Cursor_data*)pytype->tp_alloc(pytype, 0);
  if (!data) return NULL;
  Py_INCREF(Py_None);
  data->cur = NULL;
  data->pydb = Py_None;
  return (PyObject*)data;
}


/**
 * Implementation of dealloc.
 */
static void cur_dealloc(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  Py_DECREF(pydb);
  delete cur;
  Py_TYPE(data)->tp_free((PyObject*)data);
}


/**
 * Implementation of init.
 */
static int cur_init(Cursor_data* data, PyObject* pyargs, PyObject* pykwds) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return -1;
  }
  PyObject* pydb = PyTuple_GetItem(pyargs, 0);
  if (!PyObject_IsInstance(pydb, cls_db)) {
    throwinvarg();
    return -1;
  }
  DB_data* dbdata = (DB_data*)pydb;
  kc::PolyDB* db = dbdata->db;
  NativeFunction nf((DB_data*)pydb);
  g_curbur.sweap();
  data->cur = new SoftCursor(db);
  nf.cleanup();
  Py_INCREF(pydb);
  data->pydb = pydb;
  return 0;
}


/**
 * Implementation of repr.
 */
static PyObject* cur_repr(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) return PyString_FromString("<kyotocabinet.Cursor: (disabled)>");
  NativeFunction nf((DB_data*)pydb);
  kc::PolyDB* db = icur->db();
  std::string path = db->path();
  if (path.size() < 1) path = "(None)";
  std::string str;
  kc::strprintf(&str, "<kyotocabinet.Cursor: %s: ", path.c_str());
  size_t ksiz;
  char* kbuf = icur->get_key(&ksiz);
  if (kbuf) {
    str.append(kbuf, ksiz);
    delete[] kbuf;
  } else {
    str.append("(None)");
  }
  str.append(">");
  nf.cleanup();
  return PyString_FromString(str.c_str());
}


/**
 * Implementation of str.
 */
static PyObject* cur_str(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) return PyString_FromString("(disabled)");
  NativeFunction nf((DB_data*)pydb);
  kc::PolyDB* db = icur->db();
  std::string path = db->path();
  if (path.size() < 1) path = "(None)";
  std::string str;
  kc::strprintf(&str, "%s: ", path.c_str());
  size_t ksiz;
  char* kbuf = icur->get_key(&ksiz);
  if (kbuf) {
    str.append(kbuf, ksiz);
    delete[] kbuf;
  } else {
    str.append("(None)");
  }
  nf.cleanup();
  return PyString_FromString(str.c_str());
}


/**
 * Implementation of disable.
 */
static PyObject* cur_disable(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_NONE;
  NativeFunction nf((DB_data*)pydb);
  cur->disable();
  nf.cleanup();
  Py_RETURN_NONE;
}


/**
 * Implementation of accept.
 */
static PyObject* cur_accept(Cursor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1) {
    throwinvarg();
    return NULL;
  }
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_FALSE;
  if (((DB_data*)pydb)->pylock == Py_None) {
    icur->db()->set_error(kc::PolyDB::Error::INVALID, "unsupported method");
    if (db_raise((DB_data*)pydb)) return NULL;
    Py_RETURN_NONE;
  }
  PyObject* pyvisitor = PyTuple_GetItem(pyargs, 0);
  PyObject* pywritable = Py_None;
  if (argc > 1) pywritable = PyTuple_GetItem(pyargs, 1);
  PyObject* pystep = Py_None;
  if (argc > 2) pystep = PyTuple_GetItem(pyargs, 2);
  bool writable = pywritable == Py_None || PyObject_IsTrue(pywritable);
  bool step = PyObject_IsTrue(pystep);
  bool rv;
  if (PyObject_IsInstance(pyvisitor, cls_vis) || PyCallable_Check(pyvisitor)) {
    SoftVisitor visitor(pyvisitor, writable);
    NativeFunction nf((DB_data*)pydb);
    rv = icur->accept(&visitor, writable, step);
    nf.cleanup();
    PyObject* pyextype, *pyexvalue, *pyextrace;
    if (visitor.exception(&pyextype, &pyexvalue, &pyextrace)) {
      PyErr_SetObject(pyextype, pyexvalue);
      return NULL;
    }
  } else {
    throwinvarg();
    return NULL;
  }
  if (rv) Py_RETURN_TRUE;
  if (db_raise((DB_data*)pydb)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of set_value.
 */
static PyObject* cur_set_value(Cursor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 2) {
    throwinvarg();
    return NULL;
  }
  PyObject* pyvalue = PyTuple_GetItem(pyargs, 0);
  PyObject* pystep = Py_None;
  if (argc > 1) pystep = PyTuple_GetItem(pyargs, 1);
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_FALSE;
  SoftString value(pyvalue);
  bool step = PyObject_IsTrue(pystep);
  NativeFunction nf((DB_data*)pydb);
  bool rv = icur->set_value(value.ptr(), value.size(), step);
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise((DB_data*)pydb)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of remove.
 */
static PyObject* cur_remove(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_FALSE;
  NativeFunction nf((DB_data*)pydb);
  bool rv = icur->remove();
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise((DB_data*)pydb)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of get_key.
 */
static PyObject* cur_get_key(Cursor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystep = Py_None;
  if (argc > 0) pystep = PyTuple_GetItem(pyargs, 0);
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_NONE;
  bool step = PyObject_IsTrue(pystep);
  NativeFunction nf((DB_data*)pydb);
  size_t ksiz;
  char* kbuf = icur->get_key(&ksiz, step);
  nf.cleanup();
  PyObject* pyrv;
  if (kbuf) {
    pyrv = newbytes(kbuf, ksiz);
    delete[] kbuf;
  } else {
    if (db_raise((DB_data*)pydb)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of get_key_str.
 */
static PyObject* cur_get_key_str(Cursor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystep = Py_None;
  if (argc > 0) pystep = PyTuple_GetItem(pyargs, 0);
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_NONE;
  bool step = PyObject_IsTrue(pystep);
  NativeFunction nf((DB_data*)pydb);
  size_t ksiz;
  char* kbuf = icur->get_key(&ksiz, step);
  nf.cleanup();
  PyObject* pyrv;
  if (kbuf) {
    pyrv = newstring(kbuf);
    delete[] kbuf;
  } else {
    if (db_raise((DB_data*)pydb)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of get_value.
 */
static PyObject* cur_get_value(Cursor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystep = Py_None;
  if (argc > 0) pystep = PyTuple_GetItem(pyargs, 0);
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_NONE;
  bool step = PyObject_IsTrue(pystep);
  NativeFunction nf((DB_data*)pydb);
  size_t vsiz;
  char* vbuf = icur->get_value(&vsiz, step);
  nf.cleanup();
  PyObject* pyrv;
  if (vbuf) {
    pyrv = newbytes(vbuf, vsiz);
    delete[] vbuf;
  } else {
    if (db_raise((DB_data*)pydb)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of get_value_str.
 */
static PyObject* cur_get_value_str(Cursor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystep = Py_None;
  if (argc > 0) pystep = PyTuple_GetItem(pyargs, 0);
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_NONE;
  bool step = PyObject_IsTrue(pystep);
  NativeFunction nf((DB_data*)pydb);
  size_t vsiz;
  char* vbuf = icur->get_value(&vsiz, step);
  nf.cleanup();
  PyObject* pyrv;
  if (vbuf) {
    pyrv = newstring(vbuf);
    delete[] vbuf;
  } else {
    if (db_raise((DB_data*)pydb)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of get.
 */
static PyObject* cur_get(Cursor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystep = Py_None;
  if (argc > 0) pystep = PyTuple_GetItem(pyargs, 0);
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_NONE;
  bool step = PyObject_IsTrue(pystep);
  NativeFunction nf((DB_data*)pydb);
  const char* vbuf;
  size_t ksiz, vsiz;
  char* kbuf = icur->get(&ksiz, &vbuf, &vsiz, step);
  nf.cleanup();
  PyObject* pyrv;
  if (kbuf) {
    pyrv = PyTuple_New(2);
    PyObject* pykey = newbytes(kbuf, ksiz);
    PyObject* pyvalue = newbytes(vbuf, vsiz);
    PyTuple_SetItem(pyrv, 0, pykey);
    PyTuple_SetItem(pyrv, 1, pyvalue);
    delete[] kbuf;
  } else {
    if (db_raise((DB_data*)pydb)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of get_str.
 */
static PyObject* cur_get_str(Cursor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pystep = Py_None;
  if (argc > 0) pystep = PyTuple_GetItem(pyargs, 0);
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_NONE;
  bool step = PyObject_IsTrue(pystep);
  NativeFunction nf((DB_data*)pydb);
  const char* vbuf;
  size_t ksiz, vsiz;
  char* kbuf = icur->get(&ksiz, &vbuf, &vsiz, step);
  nf.cleanup();
  PyObject* pyrv;
  if (kbuf) {
    pyrv = PyTuple_New(2);
    PyObject* pykey = newstring(kbuf);
    PyObject* pyvalue = newstring(vbuf);
    PyTuple_SetItem(pyrv, 0, pykey);
    PyTuple_SetItem(pyrv, 1, pyvalue);
    delete[] kbuf;
  } else {
    if (db_raise((DB_data*)pydb)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of seize.
 */
static PyObject* cur_seize(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_NONE;
  NativeFunction nf((DB_data*)pydb);
  const char* vbuf;
  size_t ksiz, vsiz;
  char* kbuf = icur->seize(&ksiz, &vbuf, &vsiz);
  nf.cleanup();
  PyObject* pyrv;
  if (kbuf) {
    pyrv = PyTuple_New(2);
    PyObject* pykey = newbytes(kbuf, ksiz);
    PyObject* pyvalue = newbytes(vbuf, vsiz);
    PyTuple_SetItem(pyrv, 0, pykey);
    PyTuple_SetItem(pyrv, 1, pyvalue);
    delete[] kbuf;
  } else {
    if (db_raise((DB_data*)pydb)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of seize_str.
 */
static PyObject* cur_seize_str(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_NONE;
  NativeFunction nf((DB_data*)pydb);
  const char* vbuf;
  size_t ksiz, vsiz;
  char* kbuf = icur->seize(&ksiz, &vbuf, &vsiz);
  nf.cleanup();
  PyObject* pyrv;
  if (kbuf) {
    pyrv = PyTuple_New(2);
    PyObject* pykey = newstring(kbuf);
    PyObject* pyvalue = newstring(vbuf);
    PyTuple_SetItem(pyrv, 0, pykey);
    PyTuple_SetItem(pyrv, 1, pyvalue);
    delete[] kbuf;
  } else {
    if (db_raise((DB_data*)pydb)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of jump.
 */
static PyObject* cur_jump(Cursor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pykey = Py_None;
  if (argc > 0) pykey = PyTuple_GetItem(pyargs, 0);
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_FALSE;
  bool rv;
  if (pykey == Py_None) {
    NativeFunction nf((DB_data*)pydb);
    rv = icur->jump();
    nf.cleanup();
  } else {
    SoftString key(pykey);
    NativeFunction nf((DB_data*)pydb);
    rv = icur->jump(key.ptr(), key.size());
    nf.cleanup();
  }
  if (rv) Py_RETURN_TRUE;
  if (db_raise((DB_data*)pydb)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of jump_back.
 */
static PyObject* cur_jump_back(Cursor_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pykey = Py_None;
  if (argc > 0) pykey = PyTuple_GetItem(pyargs, 0);
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_FALSE;
  bool rv;
  if (pykey == Py_None) {
    NativeFunction nf((DB_data*)pydb);
    rv = icur->jump_back();
    nf.cleanup();
  } else {
    SoftString key(pykey);
    NativeFunction nf((DB_data*)pydb);
    rv = icur->jump_back(key.ptr(), key.size());
    nf.cleanup();
  }
  if (rv) Py_RETURN_TRUE;
  if (db_raise((DB_data*)pydb)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of step.
 */
static PyObject* cur_step(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_FALSE;
  NativeFunction nf((DB_data*)pydb);
  bool rv = icur->step();
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise((DB_data*)pydb)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of step_back.
 */
static PyObject* cur_step_back(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_FALSE;
  NativeFunction nf((DB_data*)pydb);
  bool rv = icur->step_back();
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise((DB_data*)pydb)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of db.
 */
static PyObject* cur_db(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_FALSE;
  Py_INCREF(data->pydb);
  return pydb;
}


/**
 * Implementation of error.
 */
static PyObject* cur_error(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) Py_RETURN_NONE;
  kc::PolyDB::Error err = icur->error();
  PyObject* pyerr = PyObject_CallMethod(mod_kc, (char*)"Error",
                                        (char*)"(Ls)", (long long)err.code(), err.message());
  return pyerr;
}


/**
 * Implementation of __iter__.
 */
static PyObject* cur_op_iter(Cursor_data* data) {
  Py_INCREF((PyObject*)data);
  return (PyObject*)data;
}


/**
 * Implementation of __next__.
 */
static PyObject* cur_op_iternext(Cursor_data* data) {
  SoftCursor* cur = data->cur;
  PyObject* pydb = data->pydb;
  kc::PolyDB::Cursor* icur = cur->cur();
  if (!icur) return NULL;
  NativeFunction nf((DB_data*)pydb);
  size_t ksiz;
  char* kbuf = icur->get_key(&ksiz, true);
  nf.cleanup();
  PyObject* pyrv;
  if (kbuf) {
    pyrv = newbytes(kbuf, ksiz);
    delete[] kbuf;
  } else {
    pyrv = NULL;
  }
  return pyrv;
}


/**
 * Define objects of the DB class.
 */
static bool define_db() {
  static PyTypeObject type_db = { PyVarObject_HEAD_INIT(NULL, 0) };
  size_t zoff = offsetof(PyTypeObject, tp_name);
  std::memset((char*)&type_db + zoff, 0, sizeof(type_db) - zoff);
  type_db.tp_name = "kyotocabinet.DB";
  type_db.tp_basicsize = sizeof(DB_data);
  type_db.tp_itemsize = 0;
  type_db.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  type_db.tp_doc = "Interface of database abstraction.";
  type_db.tp_new = db_new;
  type_db.tp_dealloc = (destructor)db_dealloc;
  type_db.tp_init = (initproc)db_init;
  type_db.tp_repr = (unaryfunc)db_repr;
  type_db.tp_str = (unaryfunc)db_str;
  static PyMethodDef db_methods[] = {
    { "error", (PyCFunction)db_error, METH_NOARGS,
      "Get the last happened error." },
    { "open", (PyCFunction)db_open, METH_VARARGS,
      "Open a database file." },
    { "close", (PyCFunction)db_close, METH_NOARGS,
      "Close the database file." },
    { "accept", (PyCFunction)db_accept, METH_VARARGS,
      "Accept a visitor to a record." },
    { "accept_bulk", (PyCFunction)db_accept_bulk, METH_VARARGS,
      "Accept a visitor to multiple records at once." },
    { "iterate", (PyCFunction)db_iterate, METH_VARARGS,
      "Iterate to accept a visitor for each record." },
    { "set", (PyCFunction)db_set, METH_VARARGS,
      "Set the value of a record." },
    { "add", (PyCFunction)db_add, METH_VARARGS,
      "Add a record." },
    { "replace", (PyCFunction)db_replace, METH_VARARGS,
      "Replace the value of a record." },
    { "append", (PyCFunction)db_append, METH_VARARGS,
      "Append the value of a record." },
    { "increment", (PyCFunction)db_increment, METH_VARARGS,
      "Add a number to the numeric integer value of a record." },
    { "increment_double", (PyCFunction)db_increment_double, METH_VARARGS,
      "Add a number to the numeric double value of a record." },
    { "cas", (PyCFunction)db_cas, METH_VARARGS,
      "Perform compare-and-swap." },
    { "remove", (PyCFunction)db_remove, METH_VARARGS,
      "Remove a record." },
    { "get", (PyCFunction)db_get, METH_VARARGS,
      "Retrieve the value of a record." },
    { "get_str", (PyCFunction)db_get_str, METH_VARARGS,
      "Retrieve the value of a record." },
    { "check", (PyCFunction)db_check, METH_VARARGS,
      "Check the existence of a record." },
    { "seize", (PyCFunction)db_seize, METH_VARARGS,
      "Retrieve the value of a record and remove it atomically." },
    { "seize_str", (PyCFunction)db_seize_str, METH_VARARGS,
      "Retrieve the value of a record and remove it atomically." },
    { "set_bulk", (PyCFunction)db_set_bulk, METH_VARARGS,
      "Store records at once." },
    { "remove_bulk", (PyCFunction)db_remove_bulk, METH_VARARGS,
      "Remove records at once." },
    { "get_bulk", (PyCFunction)db_get_bulk, METH_VARARGS,
      "Retrieve records at once." },
    { "get_bulk_str", (PyCFunction)db_get_bulk_str, METH_VARARGS,
      "Retrieve records at once." },
    { "clear", (PyCFunction)db_clear, METH_NOARGS,
      "Remove all records." },
    { "synchronize", (PyCFunction)db_synchronize, METH_VARARGS,
      "Synchronize updated contents with the file and the device." },
    { "occupy", (PyCFunction)db_occupy, METH_VARARGS,
      "Occupy database by locking and do something meanwhile." },
    { "copy", (PyCFunction)db_copy, METH_VARARGS,
      "Create a copy of the database file." },
    { "begin_transaction", (PyCFunction)db_begin_transaction, METH_VARARGS,
      "Begin transaction." },
    { "end_transaction", (PyCFunction)db_end_transaction, METH_VARARGS,
      "End transaction." },
    { "transaction", (PyCFunction)db_transaction, METH_VARARGS,
      "Perform entire transaction by a functor." },
    { "dump_snapshot", (PyCFunction)db_dump_snapshot, METH_VARARGS,
      "Dump records into a snapshot file." },
    { "load_snapshot", (PyCFunction)db_load_snapshot, METH_VARARGS,
      "Load records from a snapshot file." },
    { "count", (PyCFunction)db_count, METH_NOARGS,
      "Get the number of records." },
    { "size", (PyCFunction)db_size, METH_NOARGS,
      "Get the size of the database file." },
    { "path", (PyCFunction)db_path, METH_NOARGS,
      "Get the path of the database file." },
    { "status", (PyCFunction)db_status, METH_NOARGS,
      "Get the miscellaneous status information." },
    { "match_prefix", (PyCFunction)db_match_prefix, METH_VARARGS,
      "Get keys matching a prefix string." },
    { "match_regex", (PyCFunction)db_match_regex, METH_VARARGS,
      "Get keys matching a regular expression string." },
    { "match_similar", (PyCFunction)db_match_similar, METH_VARARGS,
      "Get keys similar to a string in terms of the levenshtein distance." },
    { "merge", (PyCFunction)db_merge, METH_VARARGS,
      "Merge records from other databases." },
    { "cursor", (PyCFunction)db_cursor, METH_NOARGS,
      "Create a cursor object." },
    { "cursor_process", (PyCFunction)db_cursor_process, METH_VARARGS,
      "Process a cursor by the block parameter." },
    { "shift", (PyCFunction)db_shift, METH_NOARGS,
      "Remove the first record." },
    { "shift_str", (PyCFunction)db_shift_str, METH_NOARGS,
      "Remove the first record." },
    { "tune_exception_rule", (PyCFunction)db_tune_exception_rule, METH_VARARGS,
      "Set the rule about throwing exception." },
    { "process", (PyCFunction)db_process, METH_VARARGS | METH_CLASS,
      "Process a database by a functor" },
    { NULL, NULL, 0, NULL }
  };
  type_db.tp_methods = db_methods;
  static PyMappingMethods type_db_map;
  std::memset(&type_db_map, 0, sizeof(type_db_map));
  type_db_map.mp_length = (lenfunc)db_op_len;
  type_db_map.mp_subscript = (binaryfunc)db_op_getitem;
  type_db_map.mp_ass_subscript = (objobjargproc)db_op_setitem;
  type_db.tp_as_mapping = &type_db_map;
  type_db.tp_iter = (getiterfunc)db_op_iter;
  if (PyType_Ready(&type_db) != 0) return false;
  cls_db = (PyObject*)&type_db;
  if (!setconstuint32(cls_db, "GEXCEPTIONAL", GEXCEPTIONAL)) return false;
  if (!setconstuint32(cls_db, "GCONCURRENT", GCONCURRENT)) return false;
  if (!setconstuint32(cls_db, "OREADER", kc::PolyDB::OREADER)) return false;
  if (!setconstuint32(cls_db, "OWRITER", kc::PolyDB::OWRITER)) return false;
  if (!setconstuint32(cls_db, "OCREATE", kc::PolyDB::OCREATE)) return false;
  if (!setconstuint32(cls_db, "OTRUNCATE", kc::PolyDB::OTRUNCATE)) return false;
  if (!setconstuint32(cls_db, "OAUTOTRAN", kc::PolyDB::OAUTOTRAN)) return false;
  if (!setconstuint32(cls_db, "OAUTOSYNC", kc::PolyDB::OAUTOSYNC)) return false;
  if (!setconstuint32(cls_db, "ONOLOCK", kc::PolyDB::ONOLOCK)) return false;
  if (!setconstuint32(cls_db, "OTRYLOCK", kc::PolyDB::OTRYLOCK)) return false;
  if (!setconstuint32(cls_db, "ONOREPAIR", kc::PolyDB::ONOREPAIR)) return false;
  if (!setconstuint32(cls_db, "MSET", kc::PolyDB::MSET)) return false;
  if (!setconstuint32(cls_db, "MADD", kc::PolyDB::MADD)) return false;
  if (!setconstuint32(cls_db, "MREPLACE", kc::PolyDB::MREPLACE)) return false;
  if (!setconstuint32(cls_db, "MAPPEND", kc::PolyDB::MAPPEND)) return false;
  Py_INCREF(cls_db);
  if (PyModule_AddObject(mod_kc, "DB", cls_db) != 0) return false;
  return true;
}


/**
 * Implementation of new.
 */
static PyObject* db_new(PyTypeObject* pytype, PyObject* pyargs, PyObject* pykwds) {
  DB_data* data = (DB_data*)pytype->tp_alloc(pytype, 0);
  if (!data) return NULL;
  data->db = NULL;
  data->exbits = 0;
  data->pylock = NULL;
  return (PyObject*)data;
}


/**
 * Implementation of dealloc.
 */
static void db_dealloc(DB_data* data) {
  kc::PolyDB* db = data->db;
  PyObject* pylock = data->pylock;
  Py_DECREF(pylock);
  delete db;
  Py_TYPE(data)->tp_free((PyObject*)data);
}


/**
 * Raise the exception of an error code.
 */
static bool db_raise(DB_data* data) {
  if (data->exbits == 0) return false;
  kc::PolyDB::Error err = data->db->error();
  uint32_t code = err.code();
  if (data->exbits & (1 << code)) {
    PyErr_Format(cls_err_children[code], "%u: %s", code, err.message());
    return true;
  }
  return false;
}


/**
 * Implementation of init.
 */
static int db_init(DB_data* data, PyObject* pyargs, PyObject* pykwds) {
  int32_t argc = PyTuple_Size(pyargs);
  PyObject* pyopts = Py_None;
  if (argc > 0) pyopts = PyTuple_GetItem(pyargs, 0);
  data->db = new kc::PolyDB();
  uint32_t opts = PyLong_Check(pyopts) ? (uint32_t)PyLong_AsLong(pyopts) : 0;
  if (opts & GEXCEPTIONAL) {
    uint32_t exbits = 0;
    exbits |= 1 << kc::PolyDB::Error::NOIMPL;
    exbits |= 1 << kc::PolyDB::Error::INVALID;
    exbits |= 1 << kc::PolyDB::Error::NOREPOS;
    exbits |= 1 << kc::PolyDB::Error::NOPERM;
    exbits |= 1 << kc::PolyDB::Error::BROKEN;
    exbits |= 1 << kc::PolyDB::Error::SYSTEM;
    exbits |= 1 << kc::PolyDB::Error::MISC;
    data->exbits = exbits;
  } else {
    data->exbits = 0;
  }
  if (opts & GCONCURRENT) {
    Py_INCREF(Py_None);
    data->pylock = Py_None;
  } else {
    data->pylock = PyObject_CallMethod(mod_th, (char*)"Lock", NULL);
  }
  return 0;
}


/**
 * Implementation of repr.
 */
static PyObject* db_repr(DB_data* data) {
  kc::PolyDB* db = data->db;
  std::string path = db->path();
  if (path.size() < 1) path = "(None)";
  std::string str;
  NativeFunction nf(data);
  kc::strprintf(&str, "<kyotocabinet.DB: %s: %lld: %lld>",
                path.c_str(), (long long)db->count(), (long long)db->size());
  nf.cleanup();
  return PyString_FromString(str.c_str());
}


/**
 * Implementation of str.
 */
static PyObject* db_str(DB_data* data) {
  kc::PolyDB* db = data->db;
  std::string path = db->path();
  if (path.size() < 1) path = "(None)";
  std::string str;
  NativeFunction nf(data);
  kc::strprintf(&str, "%s: %lld: %lld",
                path.c_str(), (long long)db->count(), (long long)db->size());
  nf.cleanup();
  return PyString_FromString(str.c_str());
}


/**
 * Implementation of error.
 */
static PyObject* db_error(DB_data* data) {
  kc::PolyDB* db = data->db;
  kc::PolyDB::Error err = db->error();
  PyObject* pyerr = PyObject_CallMethod(mod_kc, (char*)"Error",
                                        (char*)"(Ls)", (long long)err.code(), err.message());
  return pyerr;
}


/**
 * Implementation of open.
 */
static PyObject* db_open(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 2) {
    throwinvarg();
    return NULL;
  }
  PyObject* pypath = Py_None;
  if (argc > 0) pypath = PyTuple_GetItem(pyargs, 0);
  PyObject* pymode = Py_None;
  if (argc > 1) pymode = PyTuple_GetItem(pyargs, 1);
  kc::PolyDB* db = data->db;
  SoftString path(pypath);
  const char* tpath = path.size() > 0 ? path.ptr() : ":";
  uint32_t mode = PyLong_Check(pymode) ? (uint32_t)PyLong_AsLong(pymode) :
    kc::PolyDB::OWRITER | kc::PolyDB::OCREATE;
  NativeFunction nf(data);
  bool rv = db->open(tpath, mode);
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of close.
 */
static PyObject* db_close(DB_data* data) {
  kc::PolyDB* db = data->db;
  NativeFunction nf(data);
  g_curbur.sweap();
  bool rv = db->close();
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of accept.
 */
static PyObject* db_accept(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 2 || argc > 3) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  if (data->pylock == Py_None) {
    db->set_error(kc::PolyDB::Error::INVALID, "unsupported method");
    if (db_raise(data)) return NULL;
    Py_RETURN_NONE;
  }
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  SoftString key(pykey);
  PyObject* pyvisitor = PyTuple_GetItem(pyargs, 1);
  PyObject* pywritable = Py_None;
  if (argc > 2) pywritable = PyTuple_GetItem(pyargs, 2);
  bool writable = pywritable == Py_None || PyObject_IsTrue(pywritable);
  bool rv;
  if (PyObject_IsInstance(pyvisitor, cls_vis) || PyCallable_Check(pyvisitor)) {
    SoftVisitor visitor(pyvisitor, writable);
    NativeFunction nf(data);
    rv = db->accept(key.ptr(), key.size(), &visitor, writable);
    nf.cleanup();
    PyObject* pyextype, *pyexvalue, *pyextrace;
    if (visitor.exception(&pyextype, &pyexvalue, &pyextrace)) {
      PyErr_SetObject(pyextype, pyexvalue);
      return NULL;
    }
  } else {
    throwinvarg();
    return NULL;
  }
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of accept_bulk.
 */
static PyObject* db_accept_bulk(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 2 || argc > 3) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  if (data->pylock == Py_None) {
    db->set_error(kc::PolyDB::Error::INVALID, "unsupported method");
    if (db_raise(data)) return NULL;
    Py_RETURN_NONE;
  }
  PyObject* pykeys = PyTuple_GetItem(pyargs, 0);
  if (!PySequence_Check(pykeys)) {
    throwinvarg();
    return NULL;
  }
  StringVector keys;
  int32_t knum = PySequence_Length(pykeys);
  for (int32_t i = 0; i < knum; i++) {
    PyObject* pykey = PySequence_GetItem(pykeys, i);
    SoftString key(pykey);
    keys.push_back(std::string(key.ptr(), key.size()));
    Py_DECREF(pykey);
  }
  PyObject* pyvisitor = PyTuple_GetItem(pyargs, 1);
  PyObject* pywritable = Py_None;
  if (argc > 2) pywritable = PyTuple_GetItem(pyargs, 2);
  bool writable = pywritable == Py_None || PyObject_IsTrue(pywritable);
  bool rv;
  if (PyObject_IsInstance(pyvisitor, cls_vis) || PyCallable_Check(pyvisitor)) {
    SoftVisitor visitor(pyvisitor, writable);
    NativeFunction nf(data);
    rv = db->accept_bulk(keys, &visitor, writable);
    nf.cleanup();
    PyObject* pyextype, *pyexvalue, *pyextrace;
    if (visitor.exception(&pyextype, &pyexvalue, &pyextrace)) {
      PyErr_SetObject(pyextype, pyexvalue);
      return NULL;
    }
  } else {
    throwinvarg();
    return NULL;
  }
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of iterate.
 */
static PyObject* db_iterate(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  if (data->pylock == Py_None) {
    db->set_error(kc::PolyDB::Error::INVALID, "unsupported method");
    if (db_raise(data)) return NULL;
    Py_RETURN_NONE;
  }
  PyObject* pyvisitor = PyTuple_GetItem(pyargs, 0);
  PyObject* pywritable = Py_None;
  if (argc > 1) pywritable = PyTuple_GetItem(pyargs, 1);
  bool writable = pywritable == Py_None || PyObject_IsTrue(pywritable);
  bool rv;
  if (PyObject_IsInstance(pyvisitor, cls_vis) || PyCallable_Check(pyvisitor)) {
    SoftVisitor visitor(pyvisitor, writable);
    NativeFunction nf(data);
    rv = db->iterate(&visitor, writable);
    nf.cleanup();
    PyObject* pyextype, *pyexvalue, *pyextrace;
    if (visitor.exception(&pyextype, &pyexvalue, &pyextrace)) {
      PyErr_SetObject(pyextype, pyexvalue);
      return NULL;
    }
  } else {
    throwinvarg();
    return NULL;
  }
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of set.
 */
static PyObject* db_set(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  PyObject* pyvalue = PyTuple_GetItem(pyargs, 1);
  SoftString key(pykey);
  SoftString value(pyvalue);
  NativeFunction nf(data);
  bool rv = db->set(key.ptr(), key.size(), value.ptr(), value.size());
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of add.
 */
static PyObject* db_add(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  PyObject* pyvalue = PyTuple_GetItem(pyargs, 1);
  SoftString key(pykey);
  SoftString value(pyvalue);
  NativeFunction nf(data);
  bool rv = db->add(key.ptr(), key.size(), value.ptr(), value.size());
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of replace.
 */
static PyObject* db_replace(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  PyObject* pyvalue = PyTuple_GetItem(pyargs, 1);
  SoftString key(pykey);
  SoftString value(pyvalue);
  NativeFunction nf(data);
  bool rv = db->replace(key.ptr(), key.size(), value.ptr(), value.size());
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of append.
 */
static PyObject* db_append(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  PyObject* pyvalue = PyTuple_GetItem(pyargs, 1);
  SoftString key(pykey);
  SoftString value(pyvalue);
  NativeFunction nf(data);
  bool rv = db->append(key.ptr(), key.size(), value.ptr(), value.size());
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of increment.
 */
static PyObject* db_increment(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 3) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  SoftString key(pykey);
  PyObject* pynum = Py_None;
  if (argc > 1) pynum = PyTuple_GetItem(pyargs, 1);
  int64_t num = pynum == Py_None ? 0 : pyatoi(pynum);
  PyObject* pyorig = Py_None;
  if (argc > 2) pyorig = PyTuple_GetItem(pyargs, 2);
  int64_t orig = pyorig == Py_None ? 0 : pyatoi(pyorig);
  PyObject* pyrv;
  NativeFunction nf(data);
  num = db->increment(key.ptr(), key.size(), num, orig);
  nf.cleanup();
  if (num == kc::INT64MIN) {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  } else {
    pyrv = PyLong_FromLongLong(num);
  }
  return pyrv;
}


/**
 * Implementation of increment_double.
 */
static PyObject* db_increment_double(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 3) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  SoftString key(pykey);
  PyObject* pynum = Py_None;
  if (argc > 1) pynum = PyTuple_GetItem(pyargs, 1);
  double num = pynum == Py_None ? 0 : pyatof(pynum);
  PyObject* pyorig = Py_None;
  if (argc > 2) pyorig = PyTuple_GetItem(pyargs, 2);
  double orig = pyorig == Py_None ? 0 : pyatof(pyorig);
  PyObject* pyrv;
  NativeFunction nf(data);
  num = db->increment_double(key.ptr(), key.size(), num, orig);
  nf.cleanup();
  if (kc::chknan(num)) {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  } else {
    pyrv = PyFloat_FromDouble(num);
  }
  return pyrv;
}


/**
 * Implementation of cas.
 */
static PyObject* db_cas(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 3) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  SoftString key(pykey);
  PyObject* pyoval = PyTuple_GetItem(pyargs, 1);
  SoftString oval(pyoval);
  const char* ovbuf = NULL;
  size_t ovsiz = 0;
  if (pyoval != Py_None) {
    ovbuf = oval.ptr();
    ovsiz = oval.size();
  }
  PyObject* pynval = PyTuple_GetItem(pyargs, 2);
  SoftString nval(pynval);
  const char* nvbuf = NULL;
  size_t nvsiz = 0;
  if (pynval != Py_None) {
    nvbuf = nval.ptr();
    nvsiz = nval.size();
  }
  NativeFunction nf(data);
  bool rv = db->cas(key.ptr(), key.size(), ovbuf, ovsiz, nvbuf, nvsiz);
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of remove.
 */
static PyObject* db_remove(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  SoftString key(pykey);
  NativeFunction nf(data);
  bool rv = db->remove(key.ptr(), key.size());
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of get.
 */
static PyObject* db_get(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  SoftString key(pykey);
  NativeFunction nf(data);
  size_t vsiz;
  char* vbuf = db->get(key.ptr(), key.size(), &vsiz);
  nf.cleanup();
  PyObject* pyrv;
  if (vbuf) {
    pyrv = newbytes(vbuf, vsiz);
    delete[] vbuf;
  } else {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of get_str.
 */
static PyObject* db_get_str(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  SoftString key(pykey);
  NativeFunction nf(data);
  size_t vsiz;
  char* vbuf = db->get(key.ptr(), key.size(), &vsiz);
  nf.cleanup();
  PyObject* pyrv;
  if (vbuf) {
    pyrv = newstring(vbuf);
    delete[] vbuf;
  } else {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of check.
 */
static PyObject* db_check(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  SoftString key(pykey);
  NativeFunction nf(data);
  int32_t vsiz = db->check(key.ptr(), key.size());
  nf.cleanup();
  if (vsiz < 0 && db_raise(data)) return NULL;
  return PyLong_FromLongLong(vsiz);
}


/**
 * Implementation of seize.
 */
static PyObject* db_seize(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  SoftString key(pykey);
  NativeFunction nf(data);
  size_t vsiz;
  char* vbuf = db->seize(key.ptr(), key.size(), &vsiz);
  nf.cleanup();
  PyObject* pyrv;
  if (vbuf) {
    pyrv = newbytes(vbuf, vsiz);
    delete[] vbuf;
  } else {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of seize_str.
 */
static PyObject* db_seize_str(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykey = PyTuple_GetItem(pyargs, 0);
  SoftString key(pykey);
  NativeFunction nf(data);
  size_t vsiz;
  char* vbuf = db->seize(key.ptr(), key.size(), &vsiz);
  nf.cleanup();
  PyObject* pyrv;
  if (vbuf) {
    pyrv = newstring(vbuf);
    delete[] vbuf;
  } else {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of set_bulk.
 */
static PyObject* db_set_bulk(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pyrecs = PyTuple_GetItem(pyargs, 0);
  if (!PyMapping_Check(pyrecs)) {
    throwinvarg();
    return NULL;
  }
  StringMap recs;
  PyObject* pyitems = PyMapping_Items(pyrecs);
  int32_t rnum = PySequence_Length(pyitems);
  for (int32_t i = 0; i < rnum; i++) {
    PyObject* pyitem = PySequence_GetItem(pyitems, i);
    if (PyTuple_Size(pyitem) == 2) {
      PyObject* pykey = PyTuple_GetItem(pyitem, 0);
      PyObject* pyvalue = PyTuple_GetItem(pyitem, 1);
      SoftString key(pykey);
      SoftString value(pyvalue);
      recs[std::string(key.ptr(), key.size())] = std::string(value.ptr(), value.size());
    }
    Py_DECREF(pyitem);
  }
  Py_DECREF(pyitems);
  PyObject* pyatomic = Py_True;
  if (argc > 1) pyatomic = PyTuple_GetItem(pyargs, 1);
  bool atomic = PyObject_IsTrue(pyatomic);
  NativeFunction nf(data);
  int64_t rv = db->set_bulk(recs, atomic);
  nf.cleanup();
  if (rv < 0 && db_raise(data)) return NULL;
  return PyLong_FromLongLong(rv);
}


/**
 * Implementation of remove_bulk.
 */
static PyObject* db_remove_bulk(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykeys = PyTuple_GetItem(pyargs, 0);
  if (!PySequence_Check(pykeys)) {
    throwinvarg();
    return NULL;
  }
  StringVector keys;
  int32_t knum = PySequence_Length(pykeys);
  for (int32_t i = 0; i < knum; i++) {
    PyObject* pykey = PySequence_GetItem(pykeys, i);
    SoftString key(pykey);
    keys.push_back(std::string(key.ptr(), key.size()));
    Py_DECREF(pykey);
  }
  PyObject* pyatomic = Py_True;
  if (argc > 1) pyatomic = PyTuple_GetItem(pyargs, 1);
  bool atomic = PyObject_IsTrue(pyatomic);
  NativeFunction nf(data);
  int64_t rv = db->remove_bulk(keys, atomic);
  nf.cleanup();
  if (rv < 0 && db_raise(data)) return NULL;
  return PyLong_FromLongLong(rv);
}


/**
 * Implementation of get_bulk.
 */
static PyObject* db_get_bulk(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykeys = PyTuple_GetItem(pyargs, 0);
  if (!PySequence_Check(pykeys)) {
    throwinvarg();
    return NULL;
  }
  StringVector keys;
  int32_t knum = PySequence_Length(pykeys);
  for (int32_t i = 0; i < knum; i++) {
    PyObject* pykey = PySequence_GetItem(pykeys, i);
    SoftString key(pykey);
    keys.push_back(std::string(key.ptr(), key.size()));
    Py_DECREF(pykey);
  }
  PyObject* pyatomic = Py_True;
  if (argc > 1) pyatomic = PyTuple_GetItem(pyargs, 1);
  bool atomic = PyObject_IsTrue(pyatomic);
  NativeFunction nf(data);
  StringMap recs;
  int64_t rv = db->get_bulk(keys, &recs, atomic);
  nf.cleanup();
  if (rv < 0) {
    if (db_raise(data)) return NULL;
    Py_RETURN_NONE;
  }
  PyObject* pyrecs = PyDict_New();
  StringMap::const_iterator it = recs.begin();
  StringMap::const_iterator itend = recs.end();
  while (it != itend) {
    PyObject* pykey = newbytes(it->first.data(), it->first.size());
    PyObject* pyvalue = newbytes(it->second.data(), it->second.size());
    PyDict_SetItem(pyrecs, pykey, pyvalue);
    Py_DECREF(pyvalue);
    Py_DECREF(pykey);
    it++;
  }
  return pyrecs;
}


/**
 * Implementation of get_bulk_str.
 */
static PyObject* db_get_bulk_str(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pykeys = PyTuple_GetItem(pyargs, 0);
  if (!PySequence_Check(pykeys)) {
    throwinvarg();
    return NULL;
  }
  StringVector keys;
  int32_t knum = PySequence_Length(pykeys);
  for (int32_t i = 0; i < knum; i++) {
    PyObject* pykey = PySequence_GetItem(pykeys, i);
    SoftString key(pykey);
    keys.push_back(std::string(key.ptr(), key.size()));
    Py_DECREF(pykey);
  }
  PyObject* pyatomic = Py_True;
  if (argc > 1) pyatomic = PyTuple_GetItem(pyargs, 1);
  bool atomic = PyObject_IsTrue(pyatomic);
  NativeFunction nf(data);
  StringMap recs;
  int64_t rv = db->get_bulk(keys, &recs, atomic);
  nf.cleanup();
  if (rv < 0) {
    if (db_raise(data)) return NULL;
    Py_RETURN_NONE;
  }
  return maptopymap(&recs);
}


/**
 * Implementation of clear.
 */
static PyObject* db_clear(DB_data* data) {
  kc::PolyDB* db = data->db;
  NativeFunction nf(data);
  bool rv = db->clear();
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of synchronize.
 */
static PyObject* db_synchronize(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 2) {
    throwinvarg();
    return NULL;
  }
  PyObject* pyhard = Py_None;
  if (argc > 0) pyhard = PyTuple_GetItem(pyargs, 0);
  PyObject* pyproc = Py_None;
  if (argc > 1) pyproc = PyTuple_GetItem(pyargs, 1);
  kc::PolyDB* db = data->db;
  bool hard = PyObject_IsTrue(pyhard);
  bool rv;
  if (PyObject_IsInstance(pyproc, cls_fproc) || PyCallable_Check(pyproc)) {
    if (data->pylock == Py_None) {
      db->set_error(kc::PolyDB::Error::INVALID, "unsupported method");
      if (db_raise(data)) return NULL;
      Py_RETURN_NONE;
    }
    SoftFileProcessor proc(pyproc);
    NativeFunction nf(data);
    rv = db->synchronize(hard, &proc);
    nf.cleanup();
    PyObject* pyextype, *pyexvalue, *pyextrace;
    if (proc.exception(&pyextype, &pyexvalue, &pyextrace)) {
      PyErr_SetObject(pyextype, pyexvalue);
      return NULL;
    }
  } else {
    NativeFunction nf(data);
    rv = db->synchronize(hard, NULL);
    nf.cleanup();
  }
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of occupy.
 */
static PyObject* db_occupy(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 2) {
    throwinvarg();
    return NULL;
  }
  PyObject* pywritable = Py_None;
  if (argc > 0) pywritable = PyTuple_GetItem(pyargs, 0);
  PyObject* pyproc = Py_None;
  if (argc > 1) pyproc = PyTuple_GetItem(pyargs, 1);
  kc::PolyDB* db = data->db;
  bool writable = PyObject_IsTrue(pywritable);
  bool rv;
  if (PyObject_IsInstance(pyproc, cls_fproc) || PyCallable_Check(pyproc)) {
    if (data->pylock == Py_None) {
      db->set_error(kc::PolyDB::Error::INVALID, "unsupported method");
      if (db_raise(data)) return NULL;
      Py_RETURN_NONE;
    }
    SoftFileProcessor proc(pyproc);
    NativeFunction nf(data);
    rv = db->occupy(writable, &proc);
    nf.cleanup();
    PyObject* pyextype, *pyexvalue, *pyextrace;
    if (proc.exception(&pyextype, &pyexvalue, &pyextrace)) {
      PyErr_SetObject(pyextype, pyexvalue);
      return NULL;
    }
  } else {
    NativeFunction nf(data);
    rv = db->occupy(writable, NULL);
    nf.cleanup();
  }
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of copy.
 */
static PyObject* db_copy(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pydest = PyTuple_GetItem(pyargs, 0);
  kc::PolyDB* db = data->db;
  SoftString dest(pydest);
  NativeFunction nf(data);
  bool rv = db->copy(dest.ptr());
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of begin_transaction.
 */
static PyObject* db_begin_transaction(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pyhard = Py_None;
  if (argc > 0) pyhard = PyTuple_GetItem(pyargs, 0);
  kc::PolyDB* db = data->db;
  bool hard = PyObject_IsTrue(pyhard);
  bool err = false;
  while (true) {
    NativeFunction nf(data);
    bool rv = db->begin_transaction_try(hard);
    nf.cleanup();
    if (rv) break;
    if (db->error() != kc::PolyDB::Error::LOGIC) {
      err = true;
      break;
    }
    threadyield();
  }
  if (err) {
    if (db_raise(data)) return NULL;
    Py_RETURN_FALSE;
  }
  Py_RETURN_TRUE;
}


/**
 * Implementation of end_transaction.
 */
static PyObject* db_end_transaction(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc > 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pycommit = Py_None;
  if (argc > 0) pycommit = PyTuple_GetItem(pyargs, 0);
  kc::PolyDB* db = data->db;
  bool commit = pycommit == Py_None || PyObject_IsTrue(pycommit);
  NativeFunction nf(data);
  bool rv = db->end_transaction(commit);
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of transaction.
 */
static PyObject* db_transaction(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 2) {
    throwinvarg();
    return NULL;
  }
  PyObject* pyproc = PyTuple_GetItem(pyargs, 0);
  PyObject* pyhard = Py_None;
  if (argc > 1) pyhard = PyTuple_GetItem(pyargs, 1);
  PyObject* pyrv = PyObject_CallMethod((PyObject*)data, (char*)"begin_transaction",
                                       (char*)"(O)", pyhard);
  if (!pyrv) return NULL;
  if (!PyObject_IsTrue(pyrv)) {
    Py_DECREF(pyrv);
    Py_RETURN_FALSE;
  }
  Py_DECREF(pyrv);
  pyrv = PyObject_CallFunction(pyproc, NULL);
  bool commit = false;
  if (pyrv) commit = PyObject_IsTrue(pyrv);
  Py_DECREF(pyrv);
  pyrv = PyObject_CallMethod((PyObject*)data, (char*)"end_transaction",
                             (char*)"(O)", commit ? Py_True : Py_False);
  if (!pyrv) return NULL;
  if (!PyObject_IsTrue(pyrv)) {
    Py_DECREF(pyrv);
    Py_RETURN_FALSE;
  }
  Py_DECREF(pyrv);
  Py_RETURN_TRUE;
}


/**
 * Implementation of dump_snapshot.
 */
static PyObject* db_dump_snapshot(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pydest = PyTuple_GetItem(pyargs, 0);
  kc::PolyDB* db = data->db;
  SoftString dest(pydest);
  NativeFunction nf(data);
  bool rv = db->dump_snapshot(dest.ptr());
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of load_snapshot.
 */
static PyObject* db_load_snapshot(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pysrc = PyTuple_GetItem(pyargs, 0);
  kc::PolyDB* db = data->db;
  SoftString src(pysrc);
  NativeFunction nf(data);
  bool rv = db->load_snapshot(src.ptr());
  nf.cleanup();
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of count.
 */
static PyObject* db_count(DB_data* data) {
  kc::PolyDB* db = data->db;
  NativeFunction nf(data);
  int64_t count = db->count();
  nf.cleanup();
  if (count < 0 && db_raise(data)) return NULL;
  return PyLong_FromLongLong(count);
}


/**
 * Implementation of size.
 */
static PyObject* db_size(DB_data* data) {
  kc::PolyDB* db = data->db;
  NativeFunction nf(data);
  int64_t size = db->size();
  nf.cleanup();
  if (size < 0 && db_raise(data)) return NULL;
  return PyLong_FromLongLong(size);
}


/**
 * Implementation of path.
 */
static PyObject* db_path(DB_data* data) {
  kc::PolyDB* db = data->db;
  NativeFunction nf(data);
  const std::string& path = db->path();
  nf.cleanup();
  if (path.size() < 1) {
    if (db_raise(data)) return NULL;
    Py_RETURN_NONE;
  }
  return PyString_FromString(path.c_str());
}


/**
 * Implementation of status.
 */
static PyObject* db_status(DB_data* data) {
  kc::PolyDB* db = data->db;
  StringMap status;
  NativeFunction nf(data);
  bool rv = db->status(&status);
  nf.cleanup();
  if (rv) return maptopymap(&status);
  if (db_raise(data)) return NULL;
  Py_RETURN_NONE;
}


/**
 * Implementation of match_prefix.
 */
static PyObject* db_match_prefix(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pyprefix = PyTuple_GetItem(pyargs, 0);
  SoftString prefix(pyprefix);
  PyObject* pymax = Py_None;
  if (argc > 1) pymax = PyTuple_GetItem(pyargs, 1);
  int64_t max = pymax == Py_None ? -1 : pyatoi(pymax);
  PyObject* pyrv;
  NativeFunction nf(data);
  StringVector keys;
  max = db->match_prefix(std::string(prefix.ptr(), prefix.size()), &keys, max);
  nf.cleanup();
  if (max >= 0) {
    pyrv = vectortopylist(&keys);
  } else {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of match_regex.
 */
static PyObject* db_match_regex(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 2) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pyregex = PyTuple_GetItem(pyargs, 0);
  SoftString regex(pyregex);
  PyObject* pymax = Py_None;
  if (argc > 1) pymax = PyTuple_GetItem(pyargs, 1);
  int64_t max = pymax == Py_None ? -1 : pyatoi(pymax);
  PyObject* pyrv;
  NativeFunction nf(data);
  StringVector keys;
  max = db->match_regex(std::string(regex.ptr(), regex.size()), &keys, max);
  nf.cleanup();
  if (max >= 0) {
    pyrv = vectortopylist(&keys);
  } else {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of match_similar.
 */
static PyObject* db_match_similar(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 4) {
    throwinvarg();
    return NULL;
  }
  kc::PolyDB* db = data->db;
  PyObject* pyorigin = PyTuple_GetItem(pyargs, 0);
  SoftString origin(pyorigin);
  PyObject* pyrange = Py_None;
  if (argc > 1) pyrange = PyTuple_GetItem(pyargs, 1);
  int64_t range = pyrange == Py_None ? 1 : pyatoi(pyrange);
  PyObject* pyutf = Py_None;
  if (argc > 2) pyutf = PyTuple_GetItem(pyargs, 2);
  bool utf = PyObject_IsTrue(pyutf);
  PyObject* pymax = Py_None;
  if (argc > 3) pymax = PyTuple_GetItem(pyargs, 3);
  int64_t max = pymax == Py_None ? -1 : pyatoi(pymax);
  PyObject* pyrv;
  NativeFunction nf(data);
  StringVector keys;
  max = db->match_similar(std::string(origin.ptr(), origin.size()), range, utf, &keys, max);
  nf.cleanup();
  if (max >= 0) {
    pyrv = vectortopylist(&keys);
  } else {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of merge.
 */
static PyObject* db_merge(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 2) {
    throwinvarg();
    return NULL;
  }
  PyObject* pysrcary = PyTuple_GetItem(pyargs, 0);
  if (!PySequence_Check(pysrcary)) {
    throwinvarg();
    return NULL;
  }
  PyObject* pymode = Py_None;
  if (argc > 1) pymode = PyTuple_GetItem(pyargs, 1);
  uint32_t mode = PyLong_Check(pymode) ? (uint32_t)PyLong_AsLong(pymode) :
    kc::PolyDB::OWRITER | kc::PolyDB::OCREATE;
  kc::PolyDB* db = data->db;
  int32_t num = PySequence_Length(pysrcary);
  if (num < 1) Py_RETURN_TRUE;
  kc::BasicDB** srcary = new kc::BasicDB*[num];
  size_t srcnum = 0;
  for (int32_t i = 0; i < num; i++) {
    PyObject* pysrcdb = PySequence_GetItem(pysrcary, i);
    if (PyObject_IsInstance(pysrcdb, cls_db)) {
      DB_data* srcdbdata = (DB_data*)pysrcdb;
      srcary[srcnum++] = srcdbdata->db;
    }
    Py_DECREF(pysrcdb);
  }
  NativeFunction nf(data);
  bool rv = db->merge(srcary, srcnum, (kc::PolyDB::MergeMode)mode);
  nf.cleanup();
  delete[] srcary;
  if (rv) Py_RETURN_TRUE;
  if (db_raise(data)) return NULL;
  Py_RETURN_FALSE;
}


/**
 * Implementation of cursor.
 */
static PyObject* db_cursor(DB_data* data) {
  PyObject* pycur = PyObject_CallMethod(mod_kc, (char*)"Cursor",
                                        (char*)"(O)", (PyObject*)data);
  return pycur;
}


/**
 * Implementation of cursor_process.
 */
static PyObject* db_cursor_process(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pyproc = PyTuple_GetItem(pyargs, 0);
  if (!PyCallable_Check(pyproc)) {
    throwinvarg();
    return NULL;
  }
  PyObject* pycur = PyObject_CallMethod(mod_kc, (char*)"Cursor",
                                        (char*)"(O)", (PyObject*)data);
  if (!pycur) return NULL;
  PyObject* pyrv = PyObject_CallFunction(pyproc, (char*)"(O)", pycur);
  if (!pyrv) {
    Py_DECREF(pycur);
    return NULL;
  }
  Py_DECREF(pyrv);
  pyrv = PyObject_CallMethod(pycur, (char*)"disable", NULL);
  if (!pyrv) {
    Py_DECREF(pycur);
    return NULL;
  }
  Py_DECREF(pyrv);
  Py_DECREF(pycur);
  Py_RETURN_NONE;
}


/**
 * Implementation of shift.
 */
static PyObject* db_shift(DB_data* data) {
  kc::PolyDB* db = data->db;
  NativeFunction nf(data);
  char* kbuf;
  const char* vbuf;
  size_t ksiz, vsiz;
  kbuf = db_shift_impl(db, &ksiz, &vbuf, &vsiz);
  nf.cleanup();
  PyObject* pyrv;
  if (kbuf) {
    pyrv = PyTuple_New(2);
    PyObject* pykey = newbytes(kbuf, ksiz);
    PyObject* pyvalue = newbytes(vbuf, vsiz);
    PyTuple_SetItem(pyrv, 0, pykey);
    PyTuple_SetItem(pyrv, 1, pyvalue);
    delete[] kbuf;
  } else {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of shift_str.
 */
static PyObject* db_shift_str(DB_data* data) {
  kc::PolyDB* db = data->db;
  NativeFunction nf(data);
  char* kbuf;
  const char* vbuf;
  size_t ksiz, vsiz;
  kbuf = db_shift_impl(db, &ksiz, &vbuf, &vsiz);
  nf.cleanup();
  PyObject* pyrv;
  if (kbuf) {
    pyrv = PyTuple_New(2);
    PyObject* pykey = newstring(kbuf);
    PyObject* pyvalue = newstring(vbuf);
    PyTuple_SetItem(pyrv, 0, pykey);
    PyTuple_SetItem(pyrv, 1, pyvalue);
    delete[] kbuf;
  } else {
    if (db_raise(data)) return NULL;
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Common implementation of shift and shift_str.
 */
static char* db_shift_impl(kc::PolyDB* db, size_t* ksp, const char** vbp, size_t* vsp) {
  kc::PolyDB::Cursor cur(db);
  if (!cur.jump()) return NULL;
  class VisitorImpl : public kc::PolyDB::Visitor {
  public:
    explicit VisitorImpl() : kbuf_(NULL), ksiz_(0), vbuf_(NULL), vsiz_(0) {}
    char* rv(size_t* ksp, const char** vbp, size_t* vsp) {
      *ksp = ksiz_;
      *vbp = vbuf_;
      *vsp = vsiz_;
      return kbuf_;
    }
  private:
    const char* visit_full(const char* kbuf, size_t ksiz,
                           const char* vbuf, size_t vsiz, size_t* sp) {
      size_t rsiz = ksiz + 1 + vsiz + 1;
      kbuf_ = new char[rsiz];
      std::memcpy(kbuf_, kbuf, ksiz);
      kbuf_[ksiz] = '\0';
      ksiz_ = ksiz;
      vbuf_ = kbuf_ + ksiz + 1;
      std::memcpy(vbuf_, vbuf, vsiz);
      vbuf_[vsiz] = '\0';
      vsiz_ = vsiz;
      return REMOVE;
    }
    char* kbuf_;
    size_t ksiz_;
    char* vbuf_;
    size_t vsiz_;
  } visitor;
  if (!cur.accept(&visitor, true, false)) {
    *ksp = 0;
    *vbp = NULL;
    *vsp = 0;
    return NULL;
  }
  return visitor.rv(ksp, vbp, vsp);
}


/**
 * Implementation of tune_exception_rule.
 */
static PyObject* db_tune_exception_rule(DB_data* data, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc != 1) {
    throwinvarg();
    return NULL;
  }
  PyObject* pycodes = PyTuple_GetItem(pyargs, 0);
  if (!PySequence_Check(pycodes)) Py_RETURN_FALSE;
  uint32_t exbits = 0;
  int32_t num = PySequence_Length(pycodes);
  for (int32_t i = 0; i < num; i++) {
    PyObject* pycode = PySequence_GetItem(pycodes, i);
    if (PyLong_Check(pycode)) {
      uint32_t code = PyLong_AsLong(pycode);
      if (code <= kc::PolyDB::Error::MISC) exbits |= 1 << code;
    }
    Py_DECREF(pycode);
  }
  data->exbits = exbits;
  Py_RETURN_TRUE;
}


/**
 * Implementation of __len__.
 */
static Py_ssize_t db_op_len(DB_data* data) {
  kc::PolyDB* db = data->db;
  NativeFunction nf(data);
  int64_t count = db->count();
  nf.cleanup();
  return count;
}


/**
 * Implementation of __getitem__.
 */
static PyObject* db_op_getitem(DB_data* data, PyObject* pykey) {
  kc::PolyDB* db = data->db;
  SoftString key(pykey);
  NativeFunction nf(data);
  size_t vsiz;
  char* vbuf = db->get(key.ptr(), key.size(), &vsiz);
  nf.cleanup();
  PyObject* pyrv;
  if (vbuf) {
    pyrv = newbytes(vbuf, vsiz);
    delete[] vbuf;
  } else {
    Py_INCREF(Py_None);
    pyrv = Py_None;
  }
  return pyrv;
}


/**
 * Implementation of __setitem__.
 */
static int db_op_setitem(DB_data* data, PyObject* pykey, PyObject* pyvalue) {
  kc::PolyDB* db = data->db;
  if (pyvalue) {
    SoftString key(pykey);
    SoftString value(pyvalue);
    NativeFunction nf(data);
    bool rv = db->set(key.ptr(), key.size(), value.ptr(), value.size());
    nf.cleanup();
    if (rv) return 0;
    throwruntime("DB::set failed");
    return -1;
  } else {
    SoftString key(pykey);
    NativeFunction nf(data);
    bool rv = db->remove(key.ptr(), key.size());
    nf.cleanup();
    if (rv) return 0;
    throwruntime("DB::remove failed");
    return -1;
  }
}


/**
 * Implementation of __iter__.
 */
static PyObject* db_op_iter(DB_data* data) {
  PyObject* pycur = PyObject_CallMethod(mod_kc, (char*)"Cursor",
                                        (char*)"(O)", (PyObject*)data);
  PyObject* pyrv = PyObject_CallMethod(pycur, (char*)"jump", NULL);
  if (pyrv) Py_DECREF(pyrv);
  return pycur;
}


/**
 * Implementation of process.
 */
static PyObject* db_process(PyObject* cls, PyObject* pyargs) {
  int32_t argc = PyTuple_Size(pyargs);
  if (argc < 1 || argc > 4) {
    throwinvarg();
    return NULL;
  }
  PyObject* pyproc = PyTuple_GetItem(pyargs, 0);
  if (!PyCallable_Check(pyproc)) {
    throwinvarg();
    return NULL;
  }
  PyObject* pypath = Py_None;
  if (argc > 1) pypath = PyTuple_GetItem(pyargs, 1);
  PyObject* pymode = Py_None;
  if (argc > 2) pymode = PyTuple_GetItem(pyargs, 2);
  PyObject* pyopts = Py_None;
  if (argc > 3) pyopts = PyTuple_GetItem(pyargs, 3);
  PyObject* pydb = PyObject_CallMethod(mod_kc, (char*)"DB", (char*)"(O)", pyopts);
  if (!pydb) return NULL;
  PyObject* pyrv = PyObject_CallMethod(pydb, (char*)"open", (char*)"(OO)", pypath, pymode);
  if (!PyObject_IsTrue(pyrv)) {
    Py_DECREF(pyrv);
    PyObject* pyerr = PyObject_CallMethod(pydb, (char*)"error", NULL);
    Py_DECREF(pydb);
    return pyerr;
  }
  pyrv = PyObject_CallFunction(pyproc, (char*)"(O)", pydb);
  if (!pyrv) {
    Py_DECREF(pydb);
    return NULL;
  }
  Py_DECREF(pyrv);
  pyrv = PyObject_CallMethod(pydb, (char*)"close", NULL);
  if (!pyrv) {
    Py_DECREF(pydb);
    return NULL;
  }
  if (!PyObject_IsTrue(pyrv)) {
    Py_DECREF(pyrv);
    PyObject* pyerr = PyObject_CallMethod(pydb, (char*)"error", NULL);
    Py_DECREF(pydb);
    return pyerr;
  }
  Py_DECREF(pyrv);
  Py_DECREF(pydb);
  Py_RETURN_NONE;
}


}


// END OF FILE
