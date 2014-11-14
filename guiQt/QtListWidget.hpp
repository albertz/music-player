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
#include <QListWidget>

class QtListWidget : public QtBaseWidget {
	Q_OBJECT

public:
	QtListWidget(PyQtGuiObject* control);
	virtual void childIter(ChildIterCallback);

	QListWidget* listWidget;

	virtual void updateContent();

protected:
	virtual void resizeEvent(QResizeEvent *);

};

#endif
