//
//  QtObjectWidget.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include "QtObjectWidget.hpp"
#include "Builders.hpp"

RegisterControl(Object)

QtObjectWidget::QtObjectWidget(PyQtGuiObject* control) : QtBaseWidget(control) {
	PyScopedGIL gil;
	control->OuterSpace = Vec(0,0);
	Vec size = control->setupChilds();
	resize(size.x, size.y);
}
