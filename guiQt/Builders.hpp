//
//  Builders.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef MusicPlayer_guiQt_Builders_hpp
#define MusicPlayer_guiQt_Builders_hpp

#include "PyQtGuiObject.hpp"
#include <QColor>

bool buildControlObject(PyQtGuiObject* control);
bool _buildControlObject_pre(PyQtGuiObject* control);
bool _buildControlObject_post(PyQtGuiObject* control);

QColor backgroundColor(PyQtGuiObject* control);
QColor foregroundColor(PyQtGuiObject* control);

#endif
