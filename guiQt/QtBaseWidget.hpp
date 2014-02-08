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

struct QtBaseWidget : QWidget {
	// Note that we can keep all Python references only in guiObjectList because that
	// is handled in childIter: or otherwise in weakrefs.
	// Otherwise, our owner, the CocoaGuiObject.tp_traverse would not find all refs
	// and the GC would not cleanup correctly when there are cyclic refs.
	PyWeakReference* controlRef;
	bool canHaveFocus;	
	
	GuiObjectWidget(PyQtGuiObject* control);
	~GuiObjectWidget();

	virtual PyQtGuiObject* getControl(); // new ref
	virtual void updateContent();
	typedef boost::function<void(GuiObject*, bool& stop)> ChildIterCallback;
	virtual void childIter(ChildIterCallback) {}
	
	virtual void mousePressEvent(QMouseEvent*);
	
	
};


#endif
