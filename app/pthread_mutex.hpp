

#ifndef __MusicPlayer_pthread_mutex_hpp__
#define __MusicPlayer_pthread_mutex_hpp__

#include <pthread.h>
#include <assert.h>

struct Mutex {
	pthread_mutex_t mutex;
	
	Mutex() {
		mutex = (pthread_mutex_t) PTHREAD_MUTEX_INITIALIZER;
		int ret = pthread_mutex_init(&mutex, NULL);
        assert(ret == 0);		
	}
	
	~Mutex() {
		pthread_mutex_destroy(&mutex);
	}

	void lock() {
		pthread_mutex_lock(&mutex);
	}
	
	void unlock() {
		pthread_mutex_unlock(&mutex);
	}
	
	struct ScopedLock {
		pthread_mutex_t* mutex;
		ScopedLock(Mutex& _m) : mutex(&_m.mutex) { pthread_mutex_lock(mutex); }
		ScopedLock(pthread_mutex_t& _m) : mutex(&_m) { pthread_mutex_lock(mutex); }
		ScopedLock(pthread_mutex_t* _m) : mutex(_m) { pthread_mutex_lock(mutex); }
		~ScopedLock() { pthread_mutex_unlock(mutex); }
	};
	
};



#endif
