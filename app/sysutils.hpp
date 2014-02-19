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

extern "C" {

	extern const char* StartupStr;
	
	__attribute__((visibility("default")))
	bool AmIBeingDebugged();
	
	__attribute__((visibility("default")))
	void print_backtrace(int bInSignalHandler);
	
	__attribute__((visibility("default")))
	void handleFatalError(const char* msg);
	
}

// debugging stuff

void* GetPCFromUContext(void* ucontext);

typedef long ThreadId;
int GetCallstack(ThreadId threadId, void **buffer, int size);
void ExecInThread(ThreadId threadId, boost::function<void(int signum, void* siginfo, void* sigsecret)> func);


#endif
