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
	Vec size = control->setupChilds();
	control->set_size(control, size);
}

/*
@implementation ObjectControlView

- (id)initWithControl:(CocoaGuiObject*)control;
{
    self = [super initWithControl:control];
    if(!self) return nil;

	control->OuterSpace = Vec(0,0);

    return self;
}

@end
*/
