//
//  main.m
//  MusicPlayer
//
//  Created by Albert Zeyer on 21.08.12.
//  Copyright (c) 2012 Albert Zeyer. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import <Python.h>
#include <stdio.h>
#include <signal.h>


// for AmIBeingDebugged
#include <assert.h>
#include <stdbool.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/sysctl.h>


#include "sysutils.hpp"


// Based on Apple's recommended method as described in
// http://developer.apple.com/qa/qa2004/qa1361.html
extern "C"
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



std::string getResourcePath() {
	return [[[NSBundle mainBundle] resourcePath] UTF8String];
}

static NSString* getRelevantLogOutput(const std::string& filename) {
	fflush(stdout);
	FILE* f = fopen(filename.c_str(), "r");
	if(!f) return nil;
	
	NSMutableString* buffer = [NSMutableString stringWithCapacity:10000];
	char lineBuffer[4096];
	while(!feof(f) && !ferror(f)) {
		if(fgets(lineBuffer, sizeof(lineBuffer), f) == NULL) break;
		if(strcmp(lineBuffer, StartupStr) == 0)
			[buffer setString:@""];
		[buffer appendString:[NSString stringWithUTF8String:lineBuffer]];
	}
	fclose(f);
	
	return buffer;
}


extern "C"
__attribute__((visibility("default")))
void handleFatalError(const char* msg) {
	[NSApplication sharedApplication];
	[[NSRunningApplication currentApplication] activateWithOptions:NSApplicationActivateIgnoringOtherApps];
	
	NSAlert* alert = [NSAlert
					  alertWithMessageText:[NSString stringWithUTF8String:msg]
					  defaultButton:@"OK" alternateButton:@"Check homepage for new versions." otherButton:nil
					  informativeTextWithFormat:@"Unknown error."];
	[alert setAlertStyle:NSCriticalAlertStyle];
	
	if(logEnabled) {
		NSString* logOutput = getRelevantLogOutput(getTildeExpandedPath(logFilename));
		if(logOutput) {
			[alert setInformativeText:
			 @"The error is displayed below. You might want to forward this info"
			 " to the developer (mailto:albzey+musicplayer@gmail.com) so that it can be fixed."];
			
			NSTextView *textView = [[NSTextView alloc] initWithFrame:NSMakeRect(0,0,400,300)];
			[textView setFont:[NSFont userFixedPitchFontOfSize:10.0f]];
			[textView insertText:logOutput];
			[textView setEditable:NO];
			NSScrollView *scrollview = [[NSScrollView alloc] initWithFrame:NSMakeRect(0,0,400,300)];
			[scrollview setHasVerticalScroller:YES];
			[scrollview setHasHorizontalScroller:NO];
			[scrollview setAutoresizingMask:NSViewWidthSizable | NSViewHeightSizable];
			[scrollview setDocumentView:textView];
			[alert setAccessoryView:scrollview];
		}
	}
	
	NSInteger res = [alert runModal];
	if(res == NSAlertAlternateReturn) {
		[[NSWorkspace sharedWorkspace] openURL:[NSURL URLWithString:@"http://albertz.github.io/music-player/"]];
	}
	
	// No cleanup. We might call this from a signal handler or so.
	_exit(1);
}



extern int main_wrapped(int argc, char *argv[]);

int main(int argc, char *argv[])
{
	@autoreleasepool
	{
		return main_wrapped(argc, argv);		
	}
}
