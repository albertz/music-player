//
//  ThreadHangDetector.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 19.02.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include <Python.h>
#include <map>
#include <string>
#include <pthread.h>
#include <stdio.h>
#include <assert.h>

#include "ThreadHangDetector.hpp"
#include "sysutils.hpp"
#include "pthread_mutex.hpp"

static ThreadId mainThread = (ThreadId) pthread_self();


struct ThreadInfo {
	std::string name;
	float timeoutSecs;
	AbsMsTime lastLifeSignal;
};

void* backgroundThread_proc(void*);

struct ThreadHangDetector {
	Mutex mutex;
	pthread_cond_t cond;
	ThreadId backgroundThread;
	enum {
		State_Normal,
		State_JoinBackgroundThread,
		State_Exit
	} state;
	std::map<ThreadId, ThreadInfo> timers;
	
	ThreadHangDetector() {
		backgroundThread = 0;
		state = State_Normal;
		cond = (pthread_cond_t) PTHREAD_COND_INITIALIZER;
		int ret = pthread_cond_init(&cond, NULL);
		assert(ret == 0);
	}
	
	~ThreadHangDetector() {
		{
			Mutex::ScopedLock lock(mutex);
			timers.clear();
			_joinBackgroundThread();
			state = State_Exit;
		}
		pthread_cond_destroy(&cond);
	}
	
	void registerCurThread(const std::string& threadName, float timeoutSecs) {
		if(state == State_Exit) {
			printf("ThreadHangDetector_registerCurThread after exit\n");
			return;
		}
		
		ThreadId threadId = (ThreadId)pthread_self();
		
		ThreadInfo info;
		info.name = threadName;
		info.timeoutSecs = timeoutSecs;
		info.lastLifeSignal = current_abs_time();
		
		{
			Mutex::ScopedLock lock(mutex);
			timers[threadId] = info;

			while(true) {
				if(state == State_Exit) break;

				if(state == State_Normal) {
					if(!backgroundThread)
						_startBackgroundThread();
					break;
				}

				struct timespec waitTime;
				waitTime.tv_sec = 0;
				waitTime.tv_nsec = 1UL * 1000UL * 1000UL; // 1ms in nanosecs
				pthread_cond_timedwait_relative_np(&cond, &mutex.mutex, &waitTime);
			}
		}
	}
	
	void lifeSignalCurThread() {
		if(state == State_Exit) {
			printf("ThreadHangDetector_lifeSignalCurThread after exit\n");
			return;
		}
		
		ThreadId threadId = (ThreadId)pthread_self();
		
		Mutex::ScopedLock lock(mutex);
		timers[threadId].lastLifeSignal = current_abs_time();
	}
	
	void unregisterCurThread() {
		if(state == State_Exit) {
			printf("ThreadHangDetector_unregisterCurThread after exit\n");
			return;
		}
		
		ThreadId threadId = (ThreadId)pthread_self();
		
		Mutex::ScopedLock lock(mutex);
		timers.erase(threadId);

		while(true) {
			if(state == State_Exit) break;
			
			if(state == State_Normal) {
				if(timers.empty())
					_joinBackgroundThread();
				break;
			}
			
			struct timespec waitTime;
			waitTime.tv_sec = 0;
			waitTime.tv_nsec = 1UL * 1000UL * 1000UL; // 1ms in nanosecs
			pthread_cond_timedwait_relative_np(&cond, &mutex.mutex, &waitTime);
		}
	}
	
	void _startBackgroundThread() {
		assert(state == State_Normal);
		assert(!backgroundThread);
		pthread_t t = 0;
		int ret = pthread_create(&t, NULL, &backgroundThread_proc, NULL);
		assert(ret == 0);
		assert(t);
		backgroundThread = (ThreadId) t;
	}

	void _joinBackgroundThread() {
		pthread_t t = (pthread_t) backgroundThread;
		if(!t) return;
		backgroundThread = NULL;
		assert(state == State_Normal);
		state = State_JoinBackgroundThread;
		pthread_cond_broadcast(&cond);
		
		mutex.unlock();
		pthread_join(t, NULL);
		mutex.lock();
		
		assert(state == State_JoinBackgroundThread);
		state = State_Normal;
	}
	
	void _backgroundThread() {		
		Mutex::ScopedLock lock(mutex);
		while(true) {
			if(state != State_Normal) break;
			
			AbsMsTime curTime = current_abs_time();
			for(auto& it : timers) {
				ThreadId threadId = it.first;
				ThreadInfo& info = it.second;
				assert(curTime >= info.lastLifeSignal);
				if(curTime - info.lastLifeSignal > AbsMsTime(info.timeoutSecs * 1000)) {
					printf("%s Thread is hanging for more than %f secs\n", info.name.c_str(), info.timeoutSecs);
					ExecInThread(threadId, [&](int,void*,void*) {
						printf("%s Thread backtrace\n", info.name.c_str());
						print_backtrace(true, true);
					});
					ExecInThread(mainThread, [&](int,void*,void*) {
						printf("Main thread backtrace:\n");
						print_backtrace(true, false);
					});
					info.lastLifeSignal = current_abs_time(); // reset, don't immediately spam again
					// I guess we dont want the following. Not sure...
					//info.timeoutSecs = (float) pow(sqrt(info.timeoutSecs) + 1, 2); // increase quadratically
				}
			}
			
			struct timespec ts;
			ts.tv_sec = 0;
			ts.tv_nsec = 100UL * 1000UL * 1000UL; // 100ms in nanoseconds
			pthread_cond_timedwait_relative_np(&cond, &mutex.mutex, &ts);
		}
	}
};

static ThreadHangDetector detector;


void* backgroundThread_proc(void*) {
	detector._backgroundThread();
	return NULL;
}


void ThreadHangDetector_registerCurThread(const char* threadName, float timeoutSecs) {
	detector.registerCurThread(threadName, timeoutSecs);
}

void ThreadHangDetector_lifeSignalCurThread() {
	detector.lifeSignalCurThread();
}

void ThreadHangDetector_unregisterCurThread() {
	detector.unregisterCurThread();
}


