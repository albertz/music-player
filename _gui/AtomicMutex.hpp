//
//  AtomicMutex.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 20.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef MusicPlayer_AtomicMutex_hpp
#define MusicPlayer_AtomicMutex_hpp

#include <boost/atomic.hpp>
#include <boost/noncopyable.hpp>

class AtomicMutex {
	boost::atomic<bool> lock;

public:
	AtomicMutex() : lock(false) {}
	
	struct Scope : boost::noncopyable {
		AtomicMutex& m;
		Scope(AtomicMutex& _m) : m(_m) {
			while(true) {
				bool expected = false;
				if(m.lock.compare_exchange_weak(expected, true))
					break;
			}
		}
		~Scope() {
			bool oldLock = m.lock.exchange(false);
			assert(oldLock);
		}
	};
};

#endif
