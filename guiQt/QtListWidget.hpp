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
#include <Python.h>

class QtListWidget : public QtBaseWidget {
	Q_OBJECT

protected:
	class ListModel;
	class ListView;

	ListModel* listModel;
	ListView* listWidget;
	PyWeakReference* subjectListRef;
	bool autoScrolldown;

public:
	QtListWidget(PyQtGuiObject* control);
	~QtListWidget();
	virtual void childIter(ChildIterCallback);

	virtual void updateContent();

protected:
	virtual void resizeEvent(QResizeEvent *);

};

#endif
