//
//  QtBaseWidget.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer_guiQt_QtBaseWidget_hpp__
#define __MusicPlayer_guiQt_QtBaseWidget_hpp__

#include <Python.h>
#include <QWidget>
#include <boost/function.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/weak_ptr.hpp>
#include <assert.h>
#include "PyThreading.hpp"

struct GuiObject;
struct PyQtGuiObject;

struct QtBaseWidget : QWidget {
	// Note that we can keep all Python references only in guiObjectList because that
	// is handled in childIter: or otherwise in weakrefs.
	// Otherwise, our owner, the CocoaGuiObject.tp_traverse would not find all refs
	// and the GC would not cleanup correctly when there are cyclic refs.
	PyWeakReference* controlRef;
	bool canHaveFocus;	

	// We reset that in the destructor. When you hold its mutex-lock,
	// the ref is either NULL or a valid pointer to this QtBaseWidget.
	struct LockedRef {
		PyMutex mutex;
		QtBaseWidget* ptr;		
		LockedRef(QtBaseWidget& w) : ptr(&w) {}
		void reset() {
			PyScopedLock lock(mutex);
			ptr = NULL;
		}
	};	
	boost::shared_ptr<LockedRef> selfRef;

	struct WeakRef;
	
	struct ScopedRef {
		boost::shared_ptr<LockedRef> _ref;
		QtBaseWidget* ptr;
		bool lock;
		ScopedRef(WeakRef& ref);
		~ScopedRef();
		operator bool() { return ptr; }
		QtBaseWidget* operator->() { return ptr; }
	};
	
	struct WeakRef {
		typedef boost::weak_ptr<LockedRef> Ref;
		Ref ref;
		WeakRef() {}
		WeakRef(QtBaseWidget& w) { ref = w.selfRef; }
		ScopedRef scoped() { return ScopedRef(*this); }
	};
		
	QtBaseWidget(PyQtGuiObject* control);
	~QtBaseWidget();

	virtual PyQtGuiObject* getControl(); // new ref
	virtual void updateContent();
	typedef boost::function<void(GuiObject*, bool& stop)> ChildIterCallback;
	virtual void childIter(ChildIterCallback) {}
	
	virtual void mousePressEvent(QMouseEvent*);	
	// TODO: dragging
};


#endif
