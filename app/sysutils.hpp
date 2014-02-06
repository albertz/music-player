#ifndef __MusicPlayer_app_sysutils_h__
#define __MusicPlayer_app_sysutils_h__

#ifdef __cplusplus
#include <string>

extern bool logEnabled;
extern std::string logFilename;

std::string getResourcePath();

extern "C" {
#endif

bool AmIBeingDebugged();

__attribute__((visibility("default")))
void handleFatalError(const char* msg);

#ifdef __cplusplus
}
#endif

#endif
