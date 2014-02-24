//
//  GuiObject.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef MusicPlayer_GuiObject_hpp
#define MusicPlayer_GuiObject_hpp

#include <Python.h>
#include <boost/function.hpp>
#include "SafeValue.hpp"

extern PyTypeObject GuiObject_Type;

struct Vec {
	int x, y;
	Vec(int _x = 0, int _y = 0) : x(_x), y(_y) {}
	bool initFromPyObject(PyObject* obj);
	PyObject* asPyObject() const;
};

// whether to modify x,y,w,h on resize
struct Autoresize {
	bool x,y,w,h;
	Autoresize(bool _x=false, bool _y=false, bool _w=false, bool _h=false) : x(_x), y(_y), w(_w), h(_h) {}
	bool initFromPyObject(PyObject* obj);
	PyObject* asPyObject() const;
};


struct GuiObject {
	PyObject_HEAD

	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);

	int traverse(visitproc visit, void *arg) {
		Py_VISIT(__dict__);
		Py_VISIT(root);
		Py_VISIT(parent);
		Py_VISIT(attr);
		Py_VISIT(subjectObject);
		{ PyObject* o = nativeGuiObject; Py_VISIT(o); }
		if(meth_childIter) {
			int ret = 0;
			(*meth_childIter)(this, [=,&ret](GuiObject* child, bool& stop){
				ret = visit((PyObject*) child, arg);
				if(ret) stop = true;
			});
			if(ret) return ret;
		}
		return 0;
	}
	int clear() {
		Py_CLEAR(__dict__);
		Py_CLEAR(root);
		Py_CLEAR(parent);
		Py_CLEAR(attr);
		Py_CLEAR(subjectObject);
		Py_DecRef(nativeGuiObject.exchange(NULL));
		return 0;
	}
	
	GuiObject() {}
	~GuiObject() {
		if(weakreflist)
			PyObject_ClearWeakRefs((PyObject*) this);
		clear();
	}
	
	PyObject* __dict__;
	PyObject* weakreflist;
	
	GuiObject* root;
	GuiObject* parent;
	PyObject* attr; // if this is a child of something, this is the access attrib of the parent.subjectObject
	PyObject* subjectObject;
	SafeValue<PyObject*> nativeGuiObject; // safe so that we can access without the GIL

	Vec DefaultSpace;
	Vec OuterSpace;
	Vec PresetSize;
	
	// These are expected to be called without holding the GIL!
	Vec (*get_pos)(GuiObject*);
	Vec (*get_size)(GuiObject*);
	Vec (*get_innerSize)(GuiObject*);
	Autoresize (*get_autoresize)(GuiObject*);
	void (*set_pos)(GuiObject*, const Vec&);
	void (*set_size)(GuiObject*, const Vec&);
	void (*set_autoresize)(GuiObject*, const Autoresize&);
	void (*meth_addChild)(GuiObject*, GuiObject*);
	void (*meth_updateContent)(GuiObject*);
	
	// Custom. not exposed to Python right now but might later. Optional.
	// This is called *with* the Python GIL.
	void (*meth_childIter)(GuiObject*, boost::function<void(GuiObject* child, bool& stop)>); // used by tp_traverse if set
	
	// other helpers
	Vec setupChilds();
	void handleCurSelectedSong();
	void updateSubjectObject();
};

#endif
