//
//  FunctionWrapper.h
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer__FunctionWrapper__
#define __MusicPlayer__FunctionWrapper__

#include <Python.h>
#include <boost/function.hpp>

typedef boost::function<PyObject*(PyObject* args, PyObject* kw)> PyCallback;

struct FunctionWrapper {
    PyObject_HEAD
	PyCallback func;
	PyObject* weakrefs;
};

extern PyTypeObject FunctionWrapper_Type;

FunctionWrapper* newFunctionWrapper(PyCallback func);

#endif /* defined(__MusicPlayer__FunctionWrapper__) */
