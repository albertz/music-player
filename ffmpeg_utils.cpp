// ffmpeg_utils.cpp
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"
#include "Protection.hpp"
#include <unistd.h>





// this is mostly safe to call.
// returns a newly allocated c-string.
char* objStrDup(PyObject* obj) {
	PyGILState_STATE gstate = PyGILState_Ensure();
	const char* str = NULL;
	PyObject* earlierError = PyErr_Occurred();
	if(!obj)
		str = "<None>";
	else if(PyString_Check(obj))
		str = PyString_AsString(obj);
	else {
		PyObject* strObj = NULL;
		if(PyUnicode_Check(obj))
			strObj = PyUnicode_AsUTF8String(obj);
		else {
			PyObject* unicodeObj = PyObject_Unicode(obj);
			if(unicodeObj) {
				strObj = PyUnicode_AsUTF8String(unicodeObj);
				Py_DECREF(unicodeObj);
			}
		}
		if(strObj) {
			str = PyString_AsString(strObj);
			Py_DECREF(strObj);
		}
		else
			str = "<CantConvertToString>";
	}
	if(!earlierError && PyErr_Occurred())
		PyErr_Print();
	assert(str);
	char* str2 = strdup(str);
	PyGILState_Release(gstate);
	return str2;
}

// returns a newly allocated c-string.
char* objAttrStrDup(PyObject* obj, const char* attrStr) {
	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject* attrObj = PyObject_GetAttrString(obj, attrStr);
	char* str = objStrDup(attrObj);
	Py_XDECREF(attrObj);
	PyGILState_Release(gstate);
	return str;
}

std::string objAttrStr(PyObject* obj, const std::string& attrStr) {
	char* s = objAttrStrDup(obj, attrStr.c_str());
	std::string s2(s);
	free(s);
	return s2;
}



#if defined(__APPLE__)
#include <execinfo.h>

__attribute__((noinline))
void* getStackPtr(int n) {
	n += 1; // getStackPtr() itself
	void* stack[20];
	static const int Size = sizeof(stack)/sizeof(stack[0]);
	if(n >= Size) return NULL;
	int c = backtrace(stack, Size);
	if(n >= c) return NULL;
	return stack[n];
}

const char* getStackSymbol(void* pt) {
	char** s_ = backtrace_symbols(&pt, 1);
	if(!s_) return "?";
	char* s = *s_;
	free(s_);
	if(!s) return "?";
	// s = "<number>     <filename>    <interesting-part>"
	// we only want the interesting part.
	while(*s && *s != ' ') ++s; // advance the number
	while(*s && *s == ' ') ++s; // advance the spaces
	while(*s && *s != ' ') ++s; // advance the filename
	while(*s && *s == ' ') ++s; // advance the spaces	
	return s;
}

#else
void* getStackPtr(int n) { return NULL; }
const char* getStackSymbol(void* pt) { return "?"; }
#endif

size_t Buffer::pop(uint8_t* target, size_t target_size) {
	size_t c = 0;
	while(!chunks.empty()) {
		Chunk& chunk = chunks.front();
		int s = chunk.end - chunk.start;
		assert(s > 0);
		if((size_t)s > target_size) s = (int)target_size;
		memcpy(target, chunk.data + chunk.start, s);
		chunk.start += s;
		target += s;
		target_size -= s;
		c += s;
		if(chunk.start < chunk.end) {
			assert(target_size == 0);
			break;
		}
		chunks.pop_front();
	}
	_size -= c;
	return c;	
}

void Buffer::push(const uint8_t* data, size_t size) {
	_size += size;
	while(size > 0) {
		if(chunks.empty() || !chunks.back().freeDataAvailable())
			chunks.push_back();
		Chunk& chunk = chunks.back();
		size_t s = std::min(size, (size_t)chunk.freeDataAvailable());
		memcpy(chunk.data + chunk.end, data, s);
		data += s;
		size -= s;
		chunk.end += s;
	}
}


int PyDict_SetItemString_retain(PyObject* dict, const char* key, PyObject* value) {
	int ret = PyDict_SetItemString(dict, key, value);
	Py_DECREF(value);
	return ret;
}

PyMutex::PyMutex() {
	mlock(this, sizeof(*this));
	l = PyThread_allocate_lock();
	mlock(l, sizeof(*l));
	enabled = true;
}

PyMutex::~PyMutex() {
	PyThread_free_lock(l);
}

void PyMutex::lock() {
	if(enabled)
		PyThread_acquire_lock(l, WAIT_LOCK);
}

bool PyMutex::lock_nowait() {
	if(enabled)
		return PyThread_acquire_lock(l, NOWAIT_LOCK);
	else
		return true;
}

void PyMutex::unlock() {
	if(enabled)
		PyThread_release_lock(l);
}

PyScopedLock::PyScopedLock(PyMutex& m) : mutex(m) {
#ifdef MUTEX_DEBUG
	printf("%p locks %p from %s\n", (void*)PyThread_get_thread_ident(), &mutex, getStackSymbol(getStackPtr(2)));
#endif
	mutex.lock();
}

PyScopedLock::~PyScopedLock() {
#ifdef MUTEX_DEBUG
	printf("%p unlocks %p from %s\n", (void*)PyThread_get_thread_ident(), &mutex, getStackSymbol(getStackPtr(2)));
#endif
	mutex.unlock();
}

PyScopedUnlock::PyScopedUnlock(PyMutex& m) : mutex(m) {
	mutex.unlock();
}

PyScopedUnlock::~PyScopedUnlock() {
	mutex.lock();
}

PyThread::PyThread() {
	running = false;
	stopSignal = false;
	ident = -1;
}

PyThread::~PyThread() {
	stop();
}

static void PyThread_thread(void* p) {
	PyThread* t = (PyThread*)p;
	t->func(t->lock, t->stopSignal);
	{
		PyScopedLock l(t->lock);
		t->running = false;
	}
}

bool PyThread::start() {
	PyScopedLock l(lock);
	if(running) return true;
	stopSignal = false;
	running = true;
	ident = PyThread_start_new_thread(PyThread_thread, this);
	if(ident == -1) {
		running = false;
		return false;
	}
	return true;
}

void PyThread::wait() {
	while(true) {
		{
			PyScopedLock l(lock);
			if(!running) return;
		}
		usleep(1000);
	}
}

void PyThread::stop() {
	{
		PyScopedLock l(lock);
		if(!running) return;
		stopSignal = true;
	}
	wait();
}

ProtectionData::ProtectionData() {
	lockThreadIdent = 0;
	lockCounter = 0;
	isValid = true;
}

ProtectionData::~ProtectionData() {
	assert(lockCounter == 0);
	assert(lockThreadIdent == 0);
}

void ProtectionData::lock() {
	long myThreadIdent = PyThread_get_thread_ident();
	while(true) {
		PyScopedLock lock(mutex);
		if(lockCounter > 0 && lockThreadIdent != myThreadIdent) {
			usleep(10);
			continue;
		}
		lockCounter++;
		lockThreadIdent = myThreadIdent;
		return;
	}
}

void ProtectionData::unlock() {
	PyScopedLock lock(mutex);
	assert(lockCounter > 0);
	assert(lockThreadIdent == PyThread_get_thread_ident());
	lockCounter--;
}

ProtectionScope::ProtectionScope(const Protection& p) : prot(p.prot) {
	if(prot.get()) prot->lock();
}

ProtectionScope::~ProtectionScope() {
	if(prot.get()) prot->unlock();
}

void ProtectionScope::setInvalid() {
	if(prot.get()) prot->isValid = false;
}

bool ProtectionScope::isValid() {
	if(prot.get()) return prot->isValid;
	return false;
}
