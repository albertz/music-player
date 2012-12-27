// ffmpeg player output (portaudio)
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"

#include <portaudio.h>

// For setting the thread priority to realtime on MacOSX.
#ifdef __APPLE__
#include <mach/mach_init.h>
#include <mach/thread_policy.h>
#include <mach/thread_act.h> // the doc says mach/sched.h but that seems outdated...
#include <pthread.h>
#include <mach/mach_error.h>
#include <mach/mach_time.h>
#endif
static void setRealtime();


#define AUDIO_BUFFER_SIZE	(2048 * 10) // soundcard buffer


int initPlayerOutput() {
	PaError ret = Pa_Initialize();
	if(ret != paNoError)
		Py_FatalError("PortAudio init failed");
	return 0;
}


struct PlayerObject::OutStream {
	PlayerObject* const player;
	PaStream* stream;
	OutStream(PlayerObject* p) : player(p), stream(NULL) {}
	void close() {
		// we expect that we have the player lock here.
		// we must release the lock so that any thread-join can be done.
		PaStream* stream = NULL;
		std::swap(stream, this->stream);
		PyScopedUnlock unlock(player->lock);
		Pa_CloseStream(stream);
	}
	void stop() {
		// we expect that we have the lock here.
		// we must release the lock so that any thread-join can be done.
		PaStream* stream = this->stream; // buffer for unlock-scope
		PyScopedUnlock unlock(player->lock);
		Pa_StopStream(stream);
	}
};





static
int paStreamCallback(
					 const void *input, void *output,
					 unsigned long frameCount,
					 const PaStreamCallbackTimeInfo* timeInfo,
					 PaStreamCallbackFlags statusFlags,
					 void *userData )
{
	PlayerObject* player = (PlayerObject*) userData;

	// We must not hold the PyGIL here!
	PyScopedLock lock(player->lock);
	
	if(player->needRealtimeReset) {
		player->needRealtimeReset = 0;
		setRealtime();
	}

	player->readOutStream((int16_t*) output, frameCount * player->outNumChannels);
	return paContinue;
}


int PlayerObject::setPlaying(bool playing) {
	PlayerObject* player = this;
	bool oldplayingstate = false;
	Py_INCREF((PyObject*)player);
	Py_BEGIN_ALLOW_THREADS
	{
		PyScopedLock lock(player->lock);
		if(!player->outStream.get())
			player->outStream.reset(new OutStream(this));
		assert(player->outStream.get() != NULL);
		if(playing && !player->outStream->stream) {
			PaError ret;
			ret = Pa_OpenDefaultStream(
									   &player->outStream->stream,
									   0,
									   player->outNumChannels, // numOutputChannels
									   paInt16, // sampleFormat
									   player->outSamplerate, // sampleRate
									   AUDIO_BUFFER_SIZE / 2, // framesPerBuffer,
									   &paStreamCallback,
									   player //void *userData
									   );
			if(ret != paNoError) {
				PyErr_SetString(PyExc_RuntimeError, "Pa_OpenDefaultStream failed");
				if(player->outStream->stream)
					player->outStream->close();
				playing = 0;
			}
		}
		if(playing) {
			player->needRealtimeReset = 1;
			Pa_StartStream(player->outStream->stream);
		} else
			player->outStream->stop();
		oldplayingstate = player->playing;
		player->playing = playing;
	}
	Py_END_ALLOW_THREADS
	Py_DECREF((PyObject*)player);
	
	if(!PyErr_Occurred() && player->dict) {
		Py_INCREF(player->dict);
		PyObject* onPlayingStateChange = PyDict_GetItemString(player->dict, "onPlayingStateChange");
		if(onPlayingStateChange && onPlayingStateChange != Py_None) {
			Py_INCREF(onPlayingStateChange);
			
			PyObject* kwargs = PyDict_New();
			assert(kwargs);
			PyDict_SetItemString_retain(kwargs, "oldState", PyBool_FromLong(oldplayingstate));
			PyDict_SetItemString_retain(kwargs, "newState", PyBool_FromLong(playing));
			
			PyObject* retObj = PyEval_CallObjectWithKeywords(onPlayingStateChange, NULL, kwargs);
			Py_XDECREF(retObj);
			
			// errors are not fatal from the callback, so handle it now and go on
			if(PyErr_Occurred())
				PyErr_Print();
			
			Py_DECREF(kwargs);
			Py_DECREF(onPlayingStateChange);
		}
		Py_DECREF(player->dict);
	}
	
	return PyErr_Occurred() ? -1 : 0;
}



#ifdef __APPLE__
// https://developer.apple.com/library/mac/#documentation/Darwin/Conceptual/KernelProgramming/scheduler/scheduler.html
// Also, from Google Native Client, osx/nacl_thread_nice.c has some related code.
// Or, from Google Chrome, platform_thread_mac.mm.
void setRealtime() {
	kern_return_t ret;
	thread_port_t threadport = pthread_mach_thread_np(pthread_self());
	
	thread_extended_policy_data_t policy;
	policy.timeshare = 0;
	ret = thread_policy_set(threadport,
							THREAD_EXTENDED_POLICY,
							(thread_policy_t)&policy,
							THREAD_EXTENDED_POLICY_COUNT);
	if(ret != KERN_SUCCESS) {
		fprintf(stderr, "setRealtime() THREAD_EXTENDED_POLICY failed: %d, %s\n", ret, mach_error_string(ret));
		return;
	}
	
	thread_precedence_policy_data_t precedence;
	precedence.importance = 63;
	ret = thread_policy_set(threadport,
							THREAD_PRECEDENCE_POLICY,
							(thread_policy_t)&precedence,
							THREAD_PRECEDENCE_POLICY_COUNT);
	if(ret != KERN_SUCCESS) {
		fprintf(stderr, "setRealtime() THREAD_PRECEDENCE_POLICY failed: %d, %s\n", ret, mach_error_string(ret));
		return;
	}
	
	mach_timebase_info_data_t tb_info;
	mach_timebase_info(&tb_info);
	double timeFact = ((double)tb_info.denom / (double)tb_info.numer) * 1000000;
	
	thread_time_constraint_policy_data_t ttcpolicy;
	ttcpolicy.period = 2.9 * timeFact; // about 128 frames @44.1KHz
	ttcpolicy.computation = 0.75 * 2.9 * timeFact;
	ttcpolicy.constraint = 0.85 * 2.9 * timeFact;
	ttcpolicy.preemptible = 1;
	
	ret = thread_policy_set(threadport,
							THREAD_TIME_CONSTRAINT_POLICY,
							(thread_policy_t)&ttcpolicy,
							THREAD_TIME_CONSTRAINT_POLICY_COUNT);
	if(ret != KERN_SUCCESS) {
		fprintf(stderr, "setRealtime() THREAD_TIME_CONSTRAINT_POLICY failed: %d, %s\n", ret, mach_error_string(ret));
		return;
	}
}
#else
void setRealtime() {} // not implemented yet
#endif



