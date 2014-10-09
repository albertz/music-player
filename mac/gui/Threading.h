//
//  Threading.h
//  MusicPlayer
//
//  Created by Albert Zeyer on 09.10.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef MusicPlayer_Cocoa_Threading_h
#define MusicPlayer_Cocoa_Threading_h

#include <dispatch/dispatch.h>

/*
This is supposed to be the standard queue for dispatch_async().
It will internally choose between a pool of N serial queues.
This is to avoid having too much threads - which would be the case
for the concurrent queue
dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT,0).
*/
dispatch_queue_t getAsyncQueue();

#endif
