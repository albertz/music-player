
#include <Python.h>
#include <execinfo.h>
#include <dlfcn.h>
#include "sysutils.hpp"


void print_backtrace(int bInSignalHandler) {
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
			PyThreadState* tstate;
			PyGILState_STATE gstate;
			if(bInSignalHandler) {
				/* PyThreadState_Get() doesn't give the state of the current thread if
			       the thread doesn't hold the GIL. Read the thread local storage (TLS)
			       instead: call PyGILState_GetThisThreadState(). */
			    tstate = PyGILState_GetThisThreadState();				
			}
			else {
				gstate = PyGILState_Ensure();
				tstate = PyThreadState_Get();				
			}
			if(tstate != NULL)
				_Py_DumpTraceback(STDOUT_FILENO, tstate);
			else
				printf("print_backtrace: could not get Python thread state\n");
			if(!bInSignalHandler)
				PyGILState_Release(gstate);
		}
		else
			printf("print_backtrace: _Py_DumpTraceback not found\n");
	}
}
