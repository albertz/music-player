//
//  CocoaGuiObject.h
//  MusicPlayer
//
//  Created by Albert Zeyer on 18.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer__CocoaGuiObject__
#define __MusicPlayer__CocoaGuiObject__

#include "GuiObject.hpp"

struct CocoaGuiObject : GuiObject {

	int init(PyObject* args, PyObject* kwds);
	PyObject* getattr(const char* key);
	int setattr(const char* key, PyObject* value);
};

#endif /* defined(__MusicPlayer__CocoaGuiObject__) */
