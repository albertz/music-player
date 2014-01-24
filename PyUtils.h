#ifndef MP_PYUTILS_HPP
#define MP_PYUTILS_HPP

#ifdef __cplusplus
extern "C" {
#endif

// this is mostly safe to call.
// returns a newly allocated c-string.
char* objStrDup(PyObject* obj);

// returns a newly allocated c-string.
char* objAttrStrDup(PyObject* obj, const char* attrStr);

#ifdef __cplusplus
}

#include <string>

std::string objAttrStr(PyObject* obj, const std::string& attrStr);
std::string objStr(PyObject* obj);

#endif

#endif // PYUTILS_HPP
