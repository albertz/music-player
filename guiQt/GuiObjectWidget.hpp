//
//  GuiObjectWidget.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer_guiQt_GuiObjectWidget_hpp__
#define __MusicPlayer_guiQt_GuiObjectWidget_hpp__

#include "QtGuiObject.hpp"
#include <QWidget>

struct GuiObjectWidget : QWidget {
	// Note that we can keep all Python references only in guiObjectList because that
	// is handled in childIter: or otherwise in weakrefs.
	// Otherwise, our owner, the CocoaGuiObject.tp_traverse would not find all refs
	// and the GC would not cleanup correctly when there are cyclic refs.
	PyWeakReference* controlRef;
	
	GuiObjectWidget(QtGuiObject* control);
	~GuiObjectWidget();
	virtual QtGuiObject* getControl(); // new ref
	virtual void updateContent();
	
	bool canHaveFocus;	
};


#endif