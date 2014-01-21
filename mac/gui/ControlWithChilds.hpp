//
//  ControlWithChilds.h
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import <Foundation/Foundation.h>
#include "GuiObject.hpp"

typedef void (^ChildIterCallback)(GuiObject*, bool& stop);

@protocol ControlWithChilds
-(void) childIter:(ChildIterCallback) block;

@end
