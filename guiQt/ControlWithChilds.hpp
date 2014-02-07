//
//  ControlWithChilds.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MP_guiQt_ControlWithChilds_hpp__
#define __MP_guiQt_ControlWithChilds_hpp__

#include "GuiObject.hpp"
#include <functional>

typedef std::function<void(GuiObject*, bool& stop)> ChildIterCallback;

/*
@protocol ControlWithChilds
-(void) childIter:(ChildIterCallback) block;

@end
*/

#endif
