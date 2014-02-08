//
//  QtListWidget.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer_guiQt_QtListWidget_hpp__
#define __MusicPlayer_guiQt_QtListWidget_hpp__

#include "QtBaseWidget.hpp"

struct QtListWidget : QtBaseWidget {
	ListWidget(PyQtGuiObject* control);
	virtual void childIter(ChildIterCallback);
};

#endif
