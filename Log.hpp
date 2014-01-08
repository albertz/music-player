//
//  Log.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 07.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef MusicPlayer_Log_hpp
#define MusicPlayer_Log_hpp

#include <iostream>
#include <sstream>
#include <string>
#include <time.h>
#include <sys/time.h>

struct Log {
	static bool enabled;
	std::string name;
	bool needNewPrefix;

	Log(const std::string& _name) : name(_name) { resetPrefix(); }

	void resetPrefix() {
		needNewPrefix = true;
	}

	void printPrefix() {
		if(!enabled) return;
		struct timeval t;
		gettimeofday(&t, NULL);
		struct tm* now = gmtime( &t.tv_sec );
		char timestamp[256];
		strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", now);
		int millisecs = (t.tv_usec / 1000) % 1000;
		char ms_str[5];
		sprintf(ms_str, "%.03d", millisecs);
		std::cout << "[" << name.c_str() << ":" << timestamp << "." << ms_str << "] ";
	}
		
	Log& operator<<(const char* s) {
		if(!enabled) return *this;
		if(needNewPrefix) {
			printPrefix();
			needNewPrefix = false;
		}
		std::cout << s;
		return *this;
	}
	
	void flush() {
		if(!enabled) return;
		std::cout.flush();
	}
};

bool Log::enabled = false;


inline Log& endl(Log& s) {
	s << "\n";
	s.resetPrefix();
	s.flush();
	return s;
}
inline Log& operator<<(Log& s, Log& f(Log&)) { return f(s); }

template<typename T>
inline Log& operator<<(Log& s, const T& v) {
	std::stringstream ss;
	ss << v;
	s << ss.str().c_str();
	return s;
}

#endif
