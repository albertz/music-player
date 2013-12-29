//
//  main.m
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.08.12.
//  Copyright (c) 2012 Albert Zeyer. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import <Python.h>


// for AmIBeingDebugged
#include <assert.h>
#include <stdbool.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/sysctl.h>


// Based on Apple's recommended method as described in
// http://developer.apple.com/qa/qa2004/qa1361.html
bool AmIBeingDebugged()
// Returns true if the current process is being debugged (either
// running under the debugger or has a debugger attached post facto).
{
	// Initialize mib, which tells sysctl what info we want.  In this case,
	// we're looking for information about a specific process ID.
	int mib[] =
	{
		CTL_KERN,
		KERN_PROC,
		KERN_PROC_PID,
		getpid()
	};
	
	// Caution: struct kinfo_proc is marked __APPLE_API_UNSTABLE.  The source and
	// binary interfaces may change.
	struct kinfo_proc info;
	size_t info_size = sizeof ( info );
	
	int sysctl_result = sysctl ( mib, sizeof(mib) / sizeof(*mib), &info, &info_size, NULL, 0 );
	if ( sysctl_result != 0 )
		return false;
	
	// This process is being debugged if the P_TRACED flag is set.
	return ( info.kp_proc.p_flag & P_TRACED ) != 0;
}


bool forkExecProc = false;

static void addPyPath() {
	NSString* pathStr =
	[[NSString alloc]
	 initWithFormat:@"%s:%s",
	 
	 // put our Python dir first to allow to overwrite System Python stuff (if needed, for example objc)
	 [[[[NSBundle mainBundle] resourcePath] stringByAppendingString:@"/Python"] UTF8String],

	 // put the original Py_GetPath behind so that we prefer the System Python stuff if available
	 Py_GetPath()
	];
	PySys_SetPath((char*)[pathStr UTF8String]);
	if(!forkExecProc)
		printf("Python path: %s\n", [pathStr UTF8String]);
	[pathStr release];
}

static int sys_argc;
static char** sys_argv;

static bool haveArg(const char* arg) {
	for(int i = 1; i < sys_argc; ++i)
		if(strcmp(sys_argv[i], arg) == 0) {
			return true;
		}
	return false;
}

int main(int argc, char *argv[])
{
	sys_argc = argc;
	sys_argv = argv;
	//return NSApplicationMain(argc, (const char **)argv);

	NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
	
	forkExecProc = haveArg("--forkExecProc");
	bool shell = haveArg("--shell");
	bool pyShell = haveArg("--pyshell");
	bool noLog = haveArg("--nolog");
	bool help = haveArg("--help") || haveArg("-h");

	if(!forkExecProc)
		printf("Hello from MusicPlayer on MacOSX.\n");

	if(help) {
		printf(
			   "Help: Available MacOSX options:\n"
			   "  --nolog		: don't redirect stdout/stderr to log. also implied when run in debugger\n"
			   );
	}
	
	NSString* mainPyFilename = [[[NSBundle mainBundle] resourcePath] stringByAppendingString:@"/Python/main.py"];
	Py_SetProgramName(argv[0]);
	if(!forkExecProc)
		printf("Python version: %s, prefix: %s, main: %s\n", Py_GetVersion(), Py_GetPrefix(), [mainPyFilename UTF8String]);
	
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
	
	if(pyShell || shell || forkExecProc || help) {} // be quiet
	else if(AmIBeingDebugged()) {
		printf("debugger detected, not redirecting stdout/stderr\n");
	}
	else if(noLog) {
		printf("not redirecting stdout/stderr\n");
	}
	else {
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
