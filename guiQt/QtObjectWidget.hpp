//
//  ObjectControl.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer_guiQt_QtObjectWidget_hpp__
#define __MusicPlayer_guiQt_QtObjectWidget_hpp__

#include "QtBaseWidget.hpp"

struct QtObjectWidget : QtBaseWidget {
	QtObjectWidget(PyQtGuiObject* control);
	void resizeEvent(QResizeEvent *);
};

#endif
