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
#include <string>
#include <boost/function.hpp>

typedef boost::function<bool(PyQtGuiObject*)> ControlBuilderFunc;
void registerControlBuilder(const std::string& controlType, ControlBuilderFunc buildFunc);
void iterControlTypes(boost::function<void(const std::string&, ControlBuilderFunc)> callback);
ControlBuilderFunc getControlBuilder(const std::string& controlType);

#define RegisterControl(type) \
	struct _RegisterControl_ ## type { \
		_RegisterControl_ ## type() { \
			registerControlBuilder(#type, [](PyQtGuiObject* control) { \
				QtBaseWidget* widget = new Qt ## type ## Widget(control); \
				(void) widget; \
				return true; \
			}); \
		} \
	} _registerControl_ ## type ## _instance;

bool buildControl(const std::string& controlType, PyQtGuiObject* control);
bool buildControlObject(PyQtGuiObject* control);
bool _buildControlObject_pre(PyQtGuiObject* control);
bool _buildControlObject_post(PyQtGuiObject* control);

QColor backgroundColor(PyQtGuiObject* control);
QColor foregroundColor(PyQtGuiObject* control);

void setupMenu();
void setupMainWindow();

#endif
