
#include "sysutils.hpp"

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
