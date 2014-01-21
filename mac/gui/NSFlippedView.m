// NSFlippedView.m
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2013, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#import "NSFlippedView.h"

// This is work-in-progress for now.

@implementation _NSFlippedView

- (id)initWithFrame:(NSRect)frame
{
    self = [super initWithFrame:frame];
    if (self) {
        // Initialization code here.
    }
    
    return self;
}

- (void)dealloc
{
	[self setBackgroundColor:nil];
}

- (BOOL)isFlipped
{
	return YES;
}

- (void)setDrawsBackground:(BOOL)value
{
	_drawsBackground = value;
	if(value && !_backgroundColor)
		_backgroundColor = [NSColor whiteColor];
	[self setNeedsDisplay:YES];
}

- (void)setBackgroundColor:(NSColor*)value
{
	if(_backgroundColor)
		_backgroundColor = nil;
	if(value) {
		_backgroundColor = value;
		[self setNeedsDisplay:YES];
	}
}

- (NSColor*)backgroundColor
{
	return _backgroundColor;
}

- (void)setDrawsFocusRing:(BOOL)value
{
	_drawsFocusRing = value;
	[self setNeedsDisplay:YES];
}

- (BOOL)isOpaque
{
	return _drawsBackground;
}

- (void)drawRect:(NSRect)dirtyRect
{
	if(_drawsBackground && _backgroundColor) {
		[_backgroundColor setFill];
		NSRectFill(dirtyRect);
	}
	if(_drawsFocusRing) {
		NSSetFocusRingStyle(NSFocusRingOnly);
		NSRectFill([self bounds]);
	}
}

//		def acceptsFirstResponder(self):
//			return utils.attrChain(self, "control", "attr", "canHaveFocus", default=False)
//		def becomeFirstResponder(self):
//			if NSView.becomeFirstResponder(self):
//				if self.onBecomeFirstResponder: self.onBecomeFirstResponder()
//				return True
//			else:
//				return False
//		def resignFirstResponder(self):
//			if NSView.resignFirstResponder(self):
//				if self.onResignFirstResponder: self.onResignFirstResponder()				
//				return True
//			else:
//				return False
//		def keyDown_(self, ev):
//			if not self.onKeyDown or not self.onKeyDown(ev):
//				NSView.keyDown_(self, ev)
//		def keyUp_(self, ev):
//			if not self.onKeyUp or not self.onKeyUp(ev):
//				NSView.keyUp_(self, ev)
//		def mouseDown_(self, ev):
//			if not self.onMouseDown or not self.onMouseDown(ev):
//				NSView.mouseDown_(self, ev)
//		def mouseDragged_(self, ev):
//			if not self.onMouseDragged or not self.onMouseDragged(ev):
//				NSView.mouseDragged_(self, ev)
//		def mouseUp_(self, ev):
//			if not self.onMouseUp or not self.onMouseUp(ev):
//				NSView.mouseUp_(self, ev)
//		def draggingEntered_(self, sender):
//			if self.onDraggingEntered: self.onDraggingEntered(sender)
//			return self.draggingUpdated_(sender)
//		def draggingUpdated_(self, sender):
//			if self.onDraggingUpdated: self.onDraggingUpdated(sender)
//			return NSDragOperationGeneric
//		def draggingExited_(self, sender):
//			if self.onDraggingExited: self.onDraggingExited(sender)
//		def prepareForDragOperation_(self, sender):
//			return True
//		def performDragOperation_(self, sender):
//			if self.onPerformDragOperation and self.onPerformDragOperation(sender):
//				return True
//			return False

@end
