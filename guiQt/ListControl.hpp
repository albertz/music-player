//
//  ListControl.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer_guiQt_ListControl_hpp__
#define __MusicPlayer_guiQt_ListControl_hpp__

#include "GuiObjectWidget.hpp"

struct ListControlWidget : GuiObjectWidget {
	ListControlWidget(QtGuiObject* control);
	virtual void childIter(ChildIterCallback);
};

#endif
