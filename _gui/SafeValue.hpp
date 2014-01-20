//
//  SafeValue.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 20.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef MusicPlayer_SafeValue_hpp
#define MusicPlayer_SafeValue_hpp

#include "AtomicMutex.hpp"
#include <boost/atomic.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/function.hpp>
#include <assert.h>

template<typename T>
class SafeValue {
	AtomicMutex mutex;
	T value;

public:
	void set(const T& _v) {
		AtomicMutex::Scope lock(mutex);
		value = _v;
	}

	T get() {
		AtomicMutex::Scope lock(mutex);
		return value;
	}

	struct ScopedLock {
		AtomicMutex::Scope lock;
		T& value;
		ScopedLock(SafeValue& _v) : lock(_v.mutex), value(_v.value) {}
	};
	
	void operate(boost::function<void(T&)> op) {
		AtomicMutex::Scope lock(mutex);
		op(value);
	}
	
	SafeValue& operator=(const T& _v) { set(_v); return *this; }
	operator T() { return get(); }
};

#endif
