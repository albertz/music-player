//
//  Threading.m
//  MusicPlayer
//
//  Created by Albert Zeyer on 09.10.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include "Threading.h"
#include "AtomicMutex.hpp"
#include <string>
#include <vector>
#include <boost/atomic.hpp>

static boost::atomic<bool> inited;
static AtomicMutex initLock;
static boost::atomic<size_t> idx;
static std::vector<dispatch_queue_t> queues;
static const int QueueCount = 10;

static void init() {
	AtomicMutex::Scope lock(initLock);
	if(inited) return;
	queues.resize(QueueCount);
	for(int i = 0; i < QueueCount; ++i) {
		char label[20];
		sprintf(label, "async queue %i/%i", i + 1, QueueCount);
		queues[i] = dispatch_queue_create(label, DISPATCH_QUEUE_SERIAL);
	}
	inited = true;
}

dispatch_queue_t getAsyncQueue() {
	if(!inited)
		init();
	
	size_t i = idx.fetch_add(1) % QueueCount;
	return queues[i];
}

