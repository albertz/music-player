
#include <Python.h>
#include <execinfo.h>
#include <dlfcn.h>
#include "sysutils.hpp"


#include <time.h>
#include <sys/time.h>

#ifdef __MACH__
#include <mach/clock.h>
#include <mach/mach.h>
#include <mach/mach_time.h>
#endif


#ifdef __MACH__
#define ORWL_NANO (+1.0E-9)
#define ORWL_GIGA UINT64_C(1000000000)

static double orwl_timebase = 0.0;
static uint64_t orwl_timestart = 0;

AbsMsTime current_abs_time() {
	// be more careful in a multithreaded environement
	if (!orwl_timestart) {
		mach_timebase_info_data_t tb = { 0, 0 };
		mach_timebase_info(&tb);
		orwl_timebase = tb.numer;
		orwl_timebase /= tb.denom;
		orwl_timestart = mach_absolute_time();
	}
	struct timespec ts;
	double diff = (mach_absolute_time() - orwl_timestart) * orwl_timebase;
	ts.tv_sec = diff * ORWL_NANO;
	ts.tv_nsec = diff - (ts.tv_sec * ORWL_GIGA);
	return (unsigned long) ((ts.tv_sec * 1000UL)
							+ (ts.tv_nsec / 1000000UL));
}
#else

AbsMsTime current_abs_time() {
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &systemtime);
	return (unsigned long) ((ts.tv_sec * 1000UL)
							+ (ts.tv_nsec / 1000000UL));
}
#endif



void print_backtrace(int bInSignalHandler) {
	void *callstack[128];
	int framesC = backtrace(callstack, sizeof(callstack));
	printf("backtrace() returned %d addresses\n", framesC);
	backtrace_symbols_fd(callstack, framesC, STDOUT_FILENO);

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
