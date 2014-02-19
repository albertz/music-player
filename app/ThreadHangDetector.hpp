//
//  ThreadHangDetector.hpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 19.02.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#ifndef __MusicPlayer__ThreadHangDetector__
#define __MusicPlayer__ThreadHangDetector__

__attribute__((visibility("default")))
void ThreadHangDetector_registerCurThread(float timeoutSecs);

__attribute__((visibility("default")))
void ThreadHangDetector_lifeSignalCurThread();

__attribute__((visibility("default")))
void ThreadHangDetector_unregisterCurThread();

#endif /* defined(__MusicPlayer__ThreadHangDetector__) */
