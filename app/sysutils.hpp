#ifndef __MusicPlayer_app_sysutils_hpp__
#define __MusicPlayer_app_sysutils_hpp__

#ifndef __cplusplus
#error C++ only
#endif

#include <string>
#include <boost/function.hpp>

extern bool logEnabled;
extern std::string logFilename;

std::string getResourcePath();
std::string getTildeExpandedPath(const std::string& path);
bool fileExists(const std::string& path);

// no C++ mangling for these symbols
extern "C" {

	extern const char* StartupStr;
	
	__attribute__((visibility("default")))
	bool AmIBeingDebugged();
	
	__attribute__((visibility("default")))
	void print_backtrace(int bInSignalHandler, int bAllThreads);
	
	__attribute__((visibility("default")))
	void handleFatalError(const char* msg);
	
}

// debugging stuff

typedef unsigned long AbsMsTime;
AbsMsTime current_abs_time();

void* GetPCFromUContext(void* ucontext);

typedef long ThreadId;

// On Linux/Unix/Mac, the function will be called from a signal handler, running in the target thread.
void ExecInThread(ThreadId threadId, boost::function<void(int signum, void* siginfo, void* sigsecret)> func);

// Uses ExecInThread if the threadId != 0 and != current thread.
int GetCallstack(ThreadId threadId, void **buffer, int size);


#endif
