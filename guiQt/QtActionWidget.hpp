
#ifndef __MusicPlayer_guiQt_QtActionWidget_hpp__
#define __MusicPlayer_guiQt_QtActionWidget_hpp__

#include "QtBaseWidget.hpp"
#include <QPushButton>

class QtActionWidget : public QtBaseWidget {
	Q_OBJECT

public:	
	QtActionWidget(PyQtGuiObject* control);
	QPushButton* buttonWidget;
	
	void updateContent();
	void updateTitle();
	
protected:
	void resizeEvent(QResizeEvent *);

public slots:
	void onClick();
};

#endif
