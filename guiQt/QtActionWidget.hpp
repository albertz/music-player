
#ifndef __MusicPlayer_guiQt_QtActionWidget_hpp__
#define __MusicPlayer_guiQt_QtActionWidget_hpp__

#include "QtBaseWidget.hpp"
#include <QPushButton>

struct QtActionWidget : QtBaseWidget {
	QtActionWidget(PyQtGuiObject* control);
	QPushButton* buttonWidget;

public slots:
	void onClick();
};

#endif
