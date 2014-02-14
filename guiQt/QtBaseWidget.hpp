//
//  QtBaseWidget.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer_guiQt_QtBaseWidget_hpp__
#define __MusicPlayer_guiQt_QtBaseWidget_hpp__

#include "PyQtGuiObject.hpp"
#include <QWidget>
#include <boost/function.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/weak_ptr.hpp>


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
		boost::mutex mutex;
		QtBaseWidget* ptr;		
		LockedRef(QtBaseWidget& w) : ptr(&w) {}
		void reset() {
			boost::mutex::scoped_lock lock(mutex);
			ptr = NULL;
		}
	};
	boost::shared_ptr<LockedRef<QtBaseWidget> > selfRef;
	
	struct WeakRef {
		boost::weak_ptr<LockedRef<QtBaseWidget> > ref;
		WeakRef(QtBaseWidget& w) { ref = w.selfRef; }
	};
	
	struct ScopedRef {
		boost::shared_ptr<LockedRef<QtBaseWidget> > _ref;
		QtBaseWidget* ptr;
		ScopedRef(WeakRef& ref) : ptr(NULL) {
			_ref = ref.ref.lock();
			if(_ref) {
				_ref->mutex.lock();
				ptr = _ref->ptr;
			}
		}
		~ScopedRef() {
			if(_ref) _ref->mutex.unlock();
		}
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
