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
	 initWithFormat:@"%s:%s%s:%@/Python:%s",
	 Py_GetPath(),
	 Py_GetPrefix(), "/Extras/lib/python/PyObjC",
	 [[NSBundle mainBundle] resourcePath],
	 "/System/Library/Frameworks/Python.framework/Versions/Current/Extras/lib/python/PyObjC"
	 ];
	PySys_SetPath((char*)[pathStr UTF8String]);
	NSLog(@"Python path: %@", pathStr);
	[pathStr release];
}

int main(int argc, char *argv[])
{
	//return NSApplicationMain(argc, (const char **)argv);

	NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
	
	BOOL forkExecProc = NO;
	for(int i = 1; i < argc; ++i)
		if(strcmp(argv[i], "--forkExecProc") == 0) {
			forkExecProc = YES;
			break;
		}
	
	NSString* mainPyFilename = [[[NSBundle mainBundle] resourcePath] stringByAppendingString:@"/Python/main.py"];
	Py_SetProgramName(argv[0]);
	if(!forkExecProc)
		NSLog(@"Python version: %s, prefix: %s, main: %@", Py_GetVersion(), Py_GetPrefix(), mainPyFilename);
	
	Py_Initialize();
	PyEval_InitThreads();
	addPyPath();

	// Preload imp and thread. I hope to fix this bug: https://github.com/albertz/music-player/issues/8 , there was a crash in initthread which itself has called initimp
	PyObject* m = NULL;
	m = PyImport_ImportModule("imp");
	Py_XDECREF(m);
	m = PyImport_ImportModule("thread");
	Py_XDECREF(m);
	
	PySys_SetArgvEx(argc, argv, 0);
	
	if(!forkExecProc) {
		// current workaround to log stdout/stderr. see http://stackoverflow.com/questions/13104588/how-to-get-stdout-into-console-app
		printf("stdout/stderr goes to ~/Library/Logs/com.albertzeyer.MusicPlayer.log now\n");
		freopen([[@"~/Library/Logs/com.albertzeyer.MusicPlayer.log" stringByExpandingTildeInPath] UTF8String], "a", stdout);
		freopen([[@"~/Library/Logs/com.albertzeyer.MusicPlayer.log" stringByExpandingTildeInPath] UTF8String], "a", stderr);
		PyRun_SimpleString("print 'hello there'");
	}
	
	FILE* fp = fopen((char*)[mainPyFilename UTF8String], "r");
	assert(fp);
	PyRun_SimpleFile(fp, "main.py");
	
	[pool release];
	return 0;
}
