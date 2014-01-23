//
//  OneLineTextControl.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "GuiObjectView.hpp"

@interface OneLineTextControlView : NSTextField <GuiObjectProt, GuiObjectProt_customContent>

- (id)initWithControl:(CocoaGuiObject*)control;
- (PyObject*)getTextObj;
- (void)updateContent;

@end
