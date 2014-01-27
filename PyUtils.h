#ifndef MP_PYUTILS_HPP
#define MP_PYUTILS_HPP

#ifdef __cplusplus
extern "C" {
#endif

// this is mostly safe to call.
// returns a newly allocated c-string.
// doesn't need PyGIL
char* objStrDup(PyObject* obj);

// returns a newly allocated c-string.
// doesn't need PyGIL
char* objAttrStrDup(PyObject* obj, const char* attrStr);

#ifdef __cplusplus
}

#include <string>

// mostly safe, for debugging, dont need PyGIL
std::string objAttrStr(PyObject* obj, const std::string& attrStr);
std::string objStr(PyObject* obj);

// more correct. needs PyGIL
bool pyStr(PyObject* obj, std::string& str);

#endif

#endif // PYUTILS_HPP
