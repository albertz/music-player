//
//  ListControl.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import "GuiObjectView.hpp"
#import "ControlWithChilds.hpp"

@interface ListControlView : GuiObjectView <ControlWithChilds>

- (id)initWithControl:(CocoaGuiObject*)control;

@end


