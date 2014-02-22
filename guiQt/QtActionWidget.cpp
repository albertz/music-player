
#include "QtActionWidget.hpp"
#include "Builders.hpp"

RegisterControl(Action)

QtActionWidget::QtActionWidget(PyQtGuiObject* control) : QtBaseWidget(control) {
	resize(50, 25);
	buttonWidget = new QPushButton(this);
	buttonWidget->resize(frameSize());
	buttonWidget->show();
	connect(buttonWidget, SIGNAL(clicked()), this, SLOT(onClick()));
}

void QtActionWidget::onClick() {
	
}
