// NSFlippedView.h
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2013, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#import <Cocoa/Cocoa.h>

/*
This is the base of NSFlippedView in the Python guiCocoaCommon.py.
When we use this within our pure ObjC++ code, we will just use
this one and make our own specialized subclasses.

The situation about having references to Python objects here:
It's quite complicated with regards to GC. The standard ObjC wrapper
Python object PyObjCObject does not support tp_traverse, thus Python
will not know about any Python references.
A safe option would probably be to always use Python weakrefs.
The PyObjC wrapper ObjC object OC_PythonObject would probably be
the good if we needed to make some instance var or method usable
from within Python code.
Note that we also cannot use ObjC weakrefs because that is not
supported on MacOSX 10.6.
*/

@interface _NSFlippedView : NSView <NSDraggingSource>
{
@private
	BOOL _drawsBackground;
	NSColor* _backgroundColor;
	BOOL _drawsFocusRing;
}

- (void)setDrawsBackground:(BOOL)value;
- (void)setBackgroundColor:(NSColor*)value;
- (NSColor*)backgroundColor;
- (void)setDrawsFocusRing:(BOOL)value;

@end
