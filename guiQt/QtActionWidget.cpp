
#include "QtActionWidget.hpp"
#include "Builders.hpp"

RegisterControl(Action)

QtActionWidget::QtActionWidget(PyQtGuiObject* control) : QtBaseWidget(control) {	
	buttonWidget = new QPushButton(this);
	connect(buttonWidget, SIGNAL(clicked()), this, SLOT(onClick()));
}

void QtActionWidget::onClick() {
	
}
