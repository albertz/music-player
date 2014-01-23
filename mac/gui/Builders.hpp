//
//  Builders.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef MusicPlayer_Builders_hpp
#define MusicPlayer_Builders_hpp

#import "CocoaGuiObject.hpp"

bool buildControlList(CocoaGuiObject* control);
bool buildControlObject(CocoaGuiObject* control);
bool _buildControlObject_pre(CocoaGuiObject* control);
bool _buildControlObject_post(CocoaGuiObject* control);
bool buildControlOneLineText(CocoaGuiObject* control);

#endif
