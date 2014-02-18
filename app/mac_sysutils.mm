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

#include <mach_override.h>
#include <Foundation/NSDebug.h>
#include <execinfo.h>
#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <mach-o/nlist.h>


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


// Adapted from:
// https://github.com/0xced/iOS-Artwork-Extractor/blob/master/Classes/FindSymbol.c
// Adapted from MoreAddrToSym / GetFunctionName()
// http://www.opensource.apple.com/source/openmpi/openmpi-8/openmpi/opal/mca/backtrace/darwin/MoreBacktrace/MoreDebugging/MoreAddrToSym.c
void *FindSymbol(const struct mach_header *img, const char *symbol)
{
	if ((img == NULL) || (symbol == NULL))
		return NULL;

	// only 64bit supported
#if defined (__LP64__)

	if(img->magic != MH_MAGIC_64)
		// we currently only support Intel 64bit
		return NULL;

	struct mach_header_64 *image = (struct mach_header_64*) img;

	struct segment_command_64 *seg_linkedit = NULL;
	struct segment_command_64 *seg_text = NULL;
	struct symtab_command *symtab = NULL;
	unsigned int index;

	struct load_command *cmd = (struct load_command*)(image + 1);

	for (index = 0; index < image->ncmds; index += 1, cmd = (struct load_command*)((char*)cmd + cmd->cmdsize))
	{
		switch(cmd->cmd)
		{
			case LC_SEGMENT_64: {
				struct segment_command_64* segcmd = (struct segment_command_64*)cmd;
				if (!strcmp(segcmd->segname, SEG_TEXT))
					seg_text = segcmd;
				else if (!strcmp(segcmd->segname, SEG_LINKEDIT))
					seg_linkedit = segcmd;
				break;
			}

			case LC_SYMTAB:
				symtab = (struct symtab_command*)cmd;
				break;

			default:
				break;
		}
	}

	if ((seg_text == NULL) || (seg_linkedit == NULL) || (symtab == NULL))
		return NULL;

	unsigned long vm_slide = (unsigned long)image - (unsigned long)seg_text->vmaddr;
	unsigned long file_slide = ((unsigned long)seg_linkedit->vmaddr - (unsigned long)seg_text->vmaddr) - seg_linkedit->fileoff;
	struct nlist_64 *symbase = (struct nlist_64*)((unsigned long)image + (symtab->symoff + file_slide));
	char *strings = (char*)((unsigned long)image + (symtab->stroff + file_slide));
	struct nlist_64 *sym;

	for (index = 0, sym = symbase; index < symtab->nsyms; index += 1, sym += 1)
	{
		if (sym->n_un.n_strx != 0 && !strcmp(symbol, strings + sym->n_un.n_strx))
		{
			unsigned long address = vm_slide + sym->n_value;
			if (sym->n_desc & N_ARM_THUMB_DEF)
				return (void*)(address | 1);
			else
				return (void*)(address);
		}
	}   
#endif

	return NULL;
}



void print_backtrace() {
	void *callstack[128];
	int framesC = backtrace(callstack, sizeof(callstack));
	printf("backtrace() returned %d addresses\n", framesC);
	char** strs = backtrace_symbols(callstack, framesC);
	for(int i = 0; i < framesC; ++i) {
		if(strs[i])
			printf("%s\n", strs[i]);
		else
			break;
	}
	free(strs);

	{
		typedef void (*PyDumpTracebackFunc)(int fd, PyThreadState *tstate);
		PyDumpTracebackFunc _Py_DumpTraceback = (PyDumpTracebackFunc) dlsym(RTLD_DEFAULT, "_Py_DumpTraceback");
		if(_Py_DumpTraceback) {
			PyGILState_STATE gstate = PyGILState_Ensure();
			PyThreadState* tstate = PyThreadState_Get();
			if(tstate != NULL)
				_Py_DumpTraceback(STDOUT_FILENO, tstate);
			else
				printf("print_backtrace: could not get Python thread state\n");
			PyGILState_Release(gstate);
		}
		else
			printf("print_backtrace: _Py_DumpTraceback not found\n");
	}
}

typedef void (*NSAutoreleaseNoPoolFunc) (void* obj);
NSAutoreleaseNoPoolFunc __NSAutoreleaseNoPool_reenter;

void __NSAutoreleaseNoPool_replacement(void* obj) {
	__NSAutoreleaseNoPool_reenter(obj);
	
	printf("__NSAutoreleaseNoPool backtrace:\n");
	print_backtrace();	
}

void install_breakpoint_handlers() {
	kern_return_t err = 0;
	
	const struct mach_header* img = NSAddImage("/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation", NSADDIMAGE_OPTION_NONE);
	NSAutoreleaseNoPoolFunc __NSAutoreleaseNoPool = (NSAutoreleaseNoPoolFunc) FindSymbol((struct mach_header*)img, "___NSAutoreleaseNoPool");
	// Note that __NSAutoreleaseNoPool does not exist on newer MacOSX versions. I guess it got removed with ARC.
	if(__NSAutoreleaseNoPool)
		err = mach_override_ptr(
			(void*)__NSAutoreleaseNoPool,
			(void*)__NSAutoreleaseNoPool_replacement,
			(void**)&__NSAutoreleaseNoPool_reenter);
	
	// Enable some further Cocoa debugging.
	NSDebugEnabled = true;
}


extern int main_wrapped(int argc, char *argv[]);

int main(int argc, char *argv[])
{
	@autoreleasepool
	{
		return main_wrapped(argc, argv);		
	}
}
