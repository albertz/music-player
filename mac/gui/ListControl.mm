//
//  ListControl.m
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "ListControl.hpp"
#include "PythonHelpers.h"
#include <list>

@implementation ListControlView

std::list<CocoaGuiObject*> list;
NSScrollView* scrollview;
BOOL canHaveFocus;
BOOL autoScrolldown;
BOOL outstandingScrollviewUpdate;

- (id)initWithFrame:(NSRect)frame withControl:(CocoaGuiObject*)control
{
    self = [super initWithFrame:frame];
    if (self) {
        // Initialization code here.
    }

	scrollview = [[NSScrollView alloc] initWithFrame:frame];
	[scrollview setAutoresizingMask:NSViewWidthSizable|NSViewHeightSizable];
	[[scrollview contentView] setAutoresizingMask:NSViewWidthSizable|NSViewHeightSizable];
	[scrollview setDocumentView:[[_NSFlippedView alloc] initWithFrame:
								 NSMakeRect(0, 0, [scrollview contentSize].width, [scrollview contentSize].height)]];
	[(_NSFlippedView*)[scrollview documentView] setAutoresizingMask:NSViewWidthSizable];
	[scrollview setHasVerticalScroller:YES];
	[scrollview setDrawsBackground:NO];
	[scrollview setBorderType:NSBezelBorder];
	//scrollview.setBorderType_(NSGrooveBorder)

	[self setAutoresizingMask:NSViewWidthSizable|NSViewHeightSizable];
	[self addSubview:scrollview];
	//view.control = ref(control)

	{
		PyGILState_STATE gstate = PyGILState_Ensure();
		canHaveFocus = attrChain_bool_default((PyObject*) control, "attr.canHaveFocus", false);
		autoScrolldown = attrChain_bool_default((PyObject*) control, "attr.autoScrolldown", false);
		PyGILState_Release(gstate);
	}
	
	//list = [[NSMutableArray alloc] init];
	control->OuterSpace = Vec(0,0);
	outstandingScrollviewUpdate = FALSE;
	
    return self;
}

- (void)doScrollviewUpdate
{
	if(!outstandingScrollviewUpdate) return;
	
	int x=0, y=0;
	
	//[list enumerateObjectsUsingBlock:^(id subCtr, NSUInteger idx, BOOL *stop) {
	
//		for subCtr in self.control.guiObjectList:
//			w = self.scrollview.contentSize().width
//			h = subCtr.size[1]
//			subCtr.pos = (x,y)
//			subCtr.size = (w,h)
//			y += subCtr.size[1]
//		self.scrollview.documentView().setFrameSize_((self.scrollview.contentSize().width, y))
//
//		if self.control.attr.autoScrolldown:
//			self.scrollview.verticalScroller().setFloatValue_(1)
//			self.scrollview.contentView().scrollToPoint_(
//				(0, self.scrollview.documentView().frame().size.height -
//					self.scrollview.contentSize().height))

//	}];
	
	outstandingScrollviewUpdate = NO;
}

- (void)scrollviewUpdate
{
	dispatch_async(dispatch_get_main_queue(), ^{ [self doScrollviewUpdate]; });
}

- (void)drawRect:(NSRect)dirtyRect
{
	[super drawRect:dirtyRect];
	
    // Drawing code here.
}

- (BOOL)acceptsFirstResponder
{
	return canHaveFocus;
}

- (void)childIter:(ChildIterCallback)block
{
	
}

@end
