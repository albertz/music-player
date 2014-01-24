//
//  ClickableLabelControl.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 24.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "OneLineTextControl.hpp"

@interface ClickableLabelControlView : OneLineTextControlView

- (id)initWithControl:(CocoaGuiObject*)control;
- (PyObject*)getTextObj;

@end
