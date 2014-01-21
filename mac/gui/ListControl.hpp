//
//  ListControl.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import "NSFlippedView.h"
#import "ControlWithChilds.hpp"
#include "CocoaGuiObject.hpp"

@interface ListControlView : _NSFlippedView <ControlWithChilds>

- (id)initWithFrame:(NSRect)frame withControl:(CocoaGuiObject*)control;

@end


