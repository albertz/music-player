//
//  main.m
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.08.12.
//  Copyright (c) 2012 Albert Zeyer. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import <Python/Python.h>

static void addPyPath() {
	NSString* pathStr =
	[[NSString alloc]
	 initWithFormat:@"%s:%s:%@/Python",
	 Py_GetPath(),
	 "/System/Library/Frameworks/Python.framework/Versions/Current/Extras/lib/python/PyObjC",
	 [[NSBundle mainBundle] resourcePath]];
	PySys_SetPath((char*)[pathStr UTF8String]);
	[pathStr release];
}

int main(int argc, char *argv[])
{
	//return NSApplicationMain(argc, (const char **)argv);

	NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
	
	NSString* mainPyFilename = [[[NSBundle mainBundle] resourcePath] stringByAppendingString:@"/Python/main.py"];
	NSLog(@"main: %@", mainPyFilename);
	Py_SetProgramName((char*)[mainPyFilename UTF8String]);
	
	Py_Initialize();
	addPyPath();
	
	// maybe PySys_SetArgvEx ?
	
	PyRun_SimpleString("print 'hello there'");
		
	FILE* fp = fopen((char*)[mainPyFilename UTF8String], "r");
	assert(fp);
	PyRun_SimpleFile(fp, "main.py");
	
	[pool release];
	return 0;
}
