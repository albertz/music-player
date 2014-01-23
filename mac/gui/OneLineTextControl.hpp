//
//  OneLineTextControl.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "GuiObjectView.hpp"

@interface OneLineTextControlView : NSTextField <GuiObjectViewProt>

- (id)initWithControl:(CocoaGuiObject*)control;
- (PyObject*)getTextObj;

@end
