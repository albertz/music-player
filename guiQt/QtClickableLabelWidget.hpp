//
//  QtClickableLabelWidget.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 24.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer_guiQt_QtClickableLabelWidget_hpp__
#define __MusicPlayer_guiQt_QtClickableLabelWidget_hpp__

#include "QtOneLineTextWidget.hpp"

struct QtClickableLabelWidget : QtOneLineTextWidget {
	QtClickableLabelWidget(PyQtGuiObject* control);
	virtual PyObject* getTextObj();

	virtual void mousePressEvent(QMouseEvent *);
	virtual void enterEvent(QEvent *);
	virtual void leaveEvent(QEvent *);

};

#endif
