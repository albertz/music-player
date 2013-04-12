// ffmpeg player output (portaudio)
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"

#include <portaudio.h>

#ifdef __APPLE__
// PortAudio specific Mac stuff
#include "pa_mac_core.h"
#endif

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




int initPlayerOutput() {
	PaError ret = Pa_Initialize();
	if(ret != paNoError)
		Py_FatalError("PortAudio init failed");
	return 0;
}

template<typename T> struct OutPaSampleFormat{};
template<> struct OutPaSampleFormat<int16_t> {
	static const PaSampleFormat format = paInt16;
};
template<> struct OutPaSampleFormat<float32_t> {
	static const PaSampleFormat format = paFloat32;
};


struct PlayerObject::OutStream {
	PlayerObject* const player;
	PaStream* stream;
	bool needRealtimeReset; // PortAudio callback thread must set itself to realtime

	OutStream(PlayerObject* p) : player(p), stream(NULL), needRealtimeReset(false) {}
	~OutStream() { close(); }

	static int paStreamCallback(
		const void *input, void *output,
		unsigned long frameCount,
		const PaStreamCallbackTimeInfo* timeInfo,
		PaStreamCallbackFlags statusFlags,
		void *userData )
	{
		OutStream* outStream = (OutStream*) userData;
		
		// We must not hold the PyGIL here!
		PyScopedLock lock(outStream->player->lock);
		
		if(outStream->needRealtimeReset) {
			outStream->needRealtimeReset = false;
			setRealtime();
		}
		
		outStream->player->readOutStream((OUTSAMPLE_t*) output, frameCount * outStream->player->outNumChannels, NULL);
		return paContinue;
	}
	
	bool open() {
		if(stream) close();
		assert(stream == NULL);
				
		PaStreamParameters outputParameters;
		
#if defined(__APPLE__)
		PaMacCoreStreamInfo macInfo;
		PaMacCore_SetupStreamInfo( &macInfo,
			paMacCorePlayNice | paMacCorePro );
		outputParameters.hostApiSpecificStreamInfo = &macInfo;
#elif defined(__LINUX__)
		// TODO: if we have PaAlsa_EnableRealtimeScheduling in portaudio,
		// we can call that to enable RT priority with ALSA.
		// We could check dynamically via dsym.
		outputParameters.hostApiSpecificStreamInfo = NULL;
#else
		outputParameters.hostApiSpecificStreamInfo = NULL;
#endif
		
		outputParameters.device = Pa_GetDefaultOutputDevice();
		if (outputParameters.device == paNoDevice) {
			PyErr_SetString(PyExc_RuntimeError, "Pa_GetDefaultOutputDevice didn't returned a device");
			return false;
		}
		outputParameters.channelCount = player->outNumChannels;
		outputParameters.sampleFormat = OutPaSampleFormat<OUTSAMPLE_t>::format;
		outputParameters.suggestedLatency = Pa_GetDeviceInfo( outputParameters.device )->defaultHighOutputLatency;
		
		// Note about framesPerBuffer:
		// Earlier, we used (2048 * 5 * OUTSAMPLEBYTELEN) which caused
		// some random more or less rare cracking noises.
		// See here: https://github.com/albertz/music-player/issues/35
		// This doesn't seem to happen with paFramesPerBufferUnspecified.
		
		PaError ret = Pa_OpenStream(
			&stream,
			NULL, // no input
			&outputParameters,
			player->outSamplerate, // sampleRate
			paFramesPerBufferUnspecified, // framesPerBuffer,
			paClipOff | paDitherOff,
			&paStreamCallback,
			this //void *userData
			);
		
		if(ret != paNoError) {
			PyErr_Format(PyExc_RuntimeError, "Pa_OpenStream failed: (err %i) %s", ret, Pa_GetErrorText(ret));
			if(stream)
				close();
			return false;
		}

		needRealtimeReset = true;
		Pa_StartStream(stream);
		return true;
	}
	
	void close() {
		if(this->stream == NULL) return;
		// we expect that we have the player lock here.
		// we must release the lock so that any thread-join can be done.
		PaStream* stream = NULL;
		std::swap(stream, this->stream);
		PyScopedUnlock unlock(player->lock);
		Pa_CloseStream(stream);
	}
	
};






int PlayerObject::setPlaying(bool playing) {
	PlayerObject* player = this;
	bool oldplayingstate = false;
	PyScopedGIL gil;
	{
		PyScopedGIUnlock gunlock;
		
		player->workerThread.start(); // if not running yet, start
		if(!player->outStream.get())
			player->outStream.reset(new OutStream(this));
		assert(player->outStream.get() != NULL);
		
		if(soundcardOutputEnabled) {
			if(playing && !player->outStream->stream) {
				if(!player->outStream->open())
					playing = false;
			}
		}
		
		oldplayingstate = player->playing;
		player->playing = playing;
	}
	
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



