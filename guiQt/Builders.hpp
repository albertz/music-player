//
//  Builders.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef MusicPlayer_guiQt_Builders_hpp
#define MusicPlayer_guiQt_Builders_hpp

#include "QtGuiObject.hpp"
#include <QColor>

bool buildControlList(QtGuiObject* control);
bool buildControlObject(QtGuiObject* control);
bool _buildControlObject_pre(QtGuiObject* control);
bool _buildControlObject_post(QtGuiObject* control);
bool buildControlOneLineText(QtGuiObject* control);
bool buildControlClickableLabel(QtGuiObject* control);

QColor backgroundColor(QtGuiObject* control);
QColor foregroundColor(QtGuiObject* control);

#endif
