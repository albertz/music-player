// ffmpeg_utils.cpp
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"

size_t Buffer::size() const {
	size_t c = 0;
	for(auto& it : chunks)
		c += it.size();
	return c;
}

bool Buffer::empty() {
	for(auto& it : chunks)
		if(it.size() > 0)
			return false;
	return true;
}

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
	return c;	
}

void Buffer::push(const uint8_t* data, size_t size) {
	while(size > 0) {
		if(chunks.empty() || !chunks.back().freeDataAvailable())
			chunks.push_back(Chunk());
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
	l = PyThread_allocate_lock();
}

PyMutex::~PyMutex() {
	PyThread_free_lock(l);
}

void PyMutex::lock() {
	PyThread_acquire_lock(l, WAIT_LOCK);
}

bool PyMutex::lock_nowait() {
	return PyThread_acquire_lock(l, NOWAIT_LOCK);
}

void PyMutex::unlock() {
	PyThread_release_lock(l);
}

PyScopedLock::PyScopedLock(PyMutex& m) : mutex(m) {
	mutex.lock();
}

PyScopedLock::~PyScopedLock() {
	mutex.unlock();
}

PyScopedUnlock::PyScopedUnlock(PyMutex& m) : mutex(m) {
	mutex.unlock();
}

PyScopedUnlock::~PyScopedUnlock() {
	mutex.lock();
}

