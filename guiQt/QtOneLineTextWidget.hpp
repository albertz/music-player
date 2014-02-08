//
//  OneLineTextControl.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer_guiQt_QtOneLineTextWidget_hpp__
#define __MusicPlayer_guiQt_QtOneLineTextWidget_hpp__

#include "QtBaseWidget.hpp"
#include <QLineEdit>

struct QtOneLineTextWidget : QtBaseWidget, QLineEdit {
	QtOneLineTextWidget(PyQtGuiObject* control);
	
	virtual PyObject* getTextObj();
	virtual void updateContent();
};

#endif
