// ffmpeg player output (portaudio)
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"
#include "PyUtils.h"
#include "PythonHelpers.h"

#include <portaudio.h>
#include <boost/bind.hpp>
#include <boost/atomic.hpp>
#include <vector>

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
static void setRealtime(double dutyCicleMs);

/*
The implementation with the PortAudio callback was there first.
For testing, I implemented also the blocking PortAudio interface.
I had some issues which small hiccups in the audio output -
maybe the blocking PortAudio implementation can avoid them better.
For the callback, we need to minimize the locks - or better, avoid
them fully. I'm not sure it is good to depend on thread context
switches in case it is locked. This however needs some heavy redesign.
*/
#define USE_PORTAUDIO_CALLBACK 1


int initPlayerOutput() {
	PaError ret = Pa_Initialize();
	if(ret != paNoError)
		Py_FatalError("PortAudio init failed");
	return 0;
}

void reinitPlayerOutput() {
	if(Pa_Terminate() != paNoError)
		printf("Warning: Pa_Terminate() failed\n");
	initPlayerOutput();
}

template<typename T> struct OutPaSampleFormat{};
template<> struct OutPaSampleFormat<int16_t> {
	static const PaSampleFormat format = paInt16;
};
template<> struct OutPaSampleFormat<float32_t> {
	static const PaSampleFormat format = paFloat32;
};


#define LATENCY_IN_MS 100


struct PlayerObject::OutStream {
	PlayerObject* const player;
	PaStream* stream;
	boost::atomic<bool> needRealtimeReset; // PortAudio callback thread must set itself to realtime
	boost::atomic<bool> setThreadName;
	std::string soundDevice;
	PaDeviceIndex soundDeviceIdx;
	
	OutStream(PlayerObject* p) : player(p), stream(NULL), needRealtimeReset(false), setThreadName(true), soundDeviceIdx(-1) {
		mlock(this, sizeof(*this));
	}
	~OutStream() { close(false); }

#if USE_PORTAUDIO_CALLBACK
	static int paStreamCallback(
		const void *input, void *output,
		unsigned long frameCount,
		const PaStreamCallbackTimeInfo* timeInfo,
		PaStreamCallbackFlags statusFlags,
		void *userData )
	{
		OutStream* outStream = (OutStream*) userData;
		PlayerObject* player = outStream->player;
				
		if(outStream->needRealtimeReset.exchange(false))
			setRealtime(1000.0 * frameCount / player->outSamplerate);
		
		if(outStream->setThreadName.exchange(false))
			setCurThreadName("audio callback");
		
		if(statusFlags & paOutputUnderflow)
			printf("audio: paOutputUnderflow\n");
		if(statusFlags & paOutputOverflow)
			printf("audio: paOutputOverflow\n");
		
		// We must not hold the PyGIL here!
		// Also no need to hold the player lock, all is safe!

		player->readOutStream((OUTSAMPLE_t*) output, frameCount * outStream->player->outNumChannels, NULL);
		return paContinue;
	}
#else
	PyThread audioThread;
	void audioThreadProc(PyMutex& threadLock, bool& stopSignal) {
		while(true) {
			{
				PyScopedLock l(threadLock);
				if(stopSignal) return;
			}

			if(needRealtimeReset) {
				needRealtimeReset = false;
				setRealtime();
			}
			
			OUTSAMPLE_t buffer[48 * 2 * 10]; // 10ms stereo in 48khz
			size_t frameCount = 0;
			{
				PyScopedLock lock(player->lock);
				if(stopSignal) return;
				player->readOutStream(buffer, sizeof(buffer)/sizeof(OUTSAMPLE_t), NULL);
				frameCount = sizeof(buffer)/sizeof(OUTSAMPLE_t) / player->outNumChannels;
			}
			
			PaError ret = Pa_WriteStream(stream, buffer, frameCount);
			if(ret == paOutputUnderflowed)
				printf("warning: paOutputUnderflowed\n");
			else if(ret != paNoError) {
				printf("Pa_WriteStream error %i (%s)\n", ret, Pa_GetErrorText(ret));
				// sleep half a second to avoid spamming
				for(int i = 0; i < 50; ++i) {
					usleep(10 * 1000);
					PyScopedLock l(threadLock);
					if(stopSignal) return;
				}
			}
		}
	}
#endif

	static PaDeviceIndex selectSoundDevice(const std::string& preferredSoundDevice) {
		int num = Pa_GetDeviceCount();
		if(num == 0) return -1;
		
		if(!preferredSoundDevice.empty()) {
			// check for exact matches
			for(int i = 0; i < num; ++i) {
				const PaDeviceInfo* info = Pa_GetDeviceInfo(i);
				if(info->maxOutputChannels <= 0) continue;
				if(strcmp(info->name, preferredSoundDevice.c_str()) == 0)
					return i;
			}
		
			// check for substr case-insensitive matches
			for(int i = 0; i < num; ++i) {
				const PaDeviceInfo* info = Pa_GetDeviceInfo(i);
				if(info->maxOutputChannels <= 0) continue;
				if(strncasecmp(info->name, preferredSoundDevice.c_str(), preferredSoundDevice.size()) == 0)
					return i;
			}
		}
		
		// use default as fallback
		int idx = Pa_GetDefaultOutputDevice();
		if(idx >= 0 && idx < num) {
			const PaDeviceInfo* info = Pa_GetDeviceInfo(idx);
			if(info->maxOutputChannels > 0)
				return idx;
		}
		
		// strangely, there is no default, so use the first with any output channels as fallback
		for(int i = 0; i < num; ++i) {
			const PaDeviceInfo* info = Pa_GetDeviceInfo(i);
			if(info->maxOutputChannels > 0)
				return i;
		}
		
		// nothing found
		return -1;
	}

	bool open(const std::string& prefferedSoundDevice) {
		if(stream) return true;
		assert(stream == NULL);
		
		// For reference:
		// Mixxx code: http://bazaar.launchpad.net/~mixxxdevelopers/mixxx/trunk/view/head:/mixxx/src/sounddeviceportaudio.cpp
		
		PaStreamParameters outputParameters;
		
#if defined(__APPLE__)
		PaMacCoreStreamInfo macInfo;
		PaMacCore_SetupStreamInfo( &macInfo,
			paMacCorePlayNice | paMacCorePro | paMacCoreChangeDeviceParameters );
		outputParameters.hostApiSpecificStreamInfo = &macInfo;
#elif defined(__LINUX__)
		// TODO: if we have PaAlsa_EnableRealtimeScheduling in portaudio,
		// we can call that to enable RT priority with ALSA.
		// We could check dynamically via dsym.
		outputParameters.hostApiSpecificStreamInfo = NULL;
#else
		outputParameters.hostApiSpecificStreamInfo = NULL;
#endif
	
		soundDeviceIdx = selectSoundDevice(prefferedSoundDevice);
		soundDevice = "";
		if(soundDeviceIdx < 0) {
			PyScopedGIL gil;
			PyErr_SetString(PyExc_RuntimeError, "We don't have any sound device");
			return false;
		}
		soundDevice = Pa_GetDeviceInfo(soundDeviceIdx)->name;
		
		outputParameters.device = soundDeviceIdx;
		outputParameters.channelCount = player->outNumChannels;
		outputParameters.sampleFormat = OutPaSampleFormat<OUTSAMPLE_t>::format;
		
		//unsigned long bufferSize = (player->outSamplerate * player->outNumChannels / 1000) * LATENCY_IN_MS / 4;
		unsigned long bufferSize = paFramesPerBufferUnspecified; // support any buffer size
		if(bufferSize == paFramesPerBufferUnspecified)
			outputParameters.suggestedLatency = Pa_GetDeviceInfo( soundDeviceIdx )->defaultHighOutputLatency;
		else
			outputParameters.suggestedLatency = LATENCY_IN_MS / 1000.0;
			
		// Note about framesPerBuffer:
		// Earlier, we used (2048 * 5 * OUTSAMPLEBYTELEN) which caused
		// some random more or less rare cracking noises.
		// See here: https://github.com/albertz/music-player/issues/35
		// This doesn't seem to happen with paFramesPerBufferUnspecified.
		
		while(true) {
			PaError ret = Pa_OpenStream(
				&stream,
				NULL, // no input
				&outputParameters,
				player->outSamplerate, // sampleRate
				bufferSize,
				paClipOff | paDitherOff,
#if USE_PORTAUDIO_CALLBACK
				&paStreamCallback,
#else
				NULL,
#endif
				this //void *userData
				);
			
			if(ret != paNoError) {
				if(stream)
					close(false);
				if(outputParameters.device != Pa_GetDefaultOutputDevice() && Pa_GetDefaultOutputDevice() >= 0) {
					printf("Pa_OpenStream (%s) failed: (err %i) %s. trying again with default device.\n", soundDevice.c_str(), ret, Pa_GetErrorText(ret));
					outputParameters.device = Pa_GetDefaultOutputDevice();
					continue;
				}
				else {
					PyScopedGIL gil;
					PyErr_Format(PyExc_RuntimeError, "Pa_OpenStream (%s) failed: (err %i) %s", soundDevice.c_str(), ret, Pa_GetErrorText(ret));
				}
				return false;
			}
			break;
		}

		needRealtimeReset = true;
		setThreadName = true;
		Pa_StartStream(stream);

#if !USE_PORTAUDIO_CALLBACK
		audioThread.func = boost::bind(&OutStream::audioThreadProc, this, _1, _2);
		audioThread.start();
#endif
		return true;
	}
	
	void close(bool waitForPendingAudioBuffers) {
		if(this->stream == NULL) return;
		// we expect that we have the player lock here.
		// reset fader.
		player->fader.change(0,0);
		// we must release the player lock so that any thread-join can be done.
		PaStream* stream = NULL;
		std::swap(stream, this->stream);
		PyScopedUnlock unlock(player->lock);
#if !USE_PORTAUDIO_CALLBACK
		audioThread.stop();
#endif
		if(waitForPendingAudioBuffers)
			Pa_StopStream(stream);
		Pa_CloseStream(stream);
	}
	
	bool isOpen() const { return stream != NULL; }
	
};




bool PlayerObject::openOutStream() {
	if(!soundcardOutputEnabled)
		return true;
	
	if(!outStream.get())
		outStream.reset(new OutStream(this));
	assert(outStream.get() != NULL);

	return outStream->open(preferredSoundDevice);
}

bool PlayerObject::isOutStreamOpen() {
	if(!outStream.get()) return false;
	return outStream->isOpen();
}

void PlayerObject::closeOutStream(bool waitForPendingAudioBuffers) {
	if(!outStream.get()) return;
	if(!outStream->isOpen()) return;
	outStream->close(waitForPendingAudioBuffers);
}


int PlayerObject::setPlaying(bool playing) {
	PlayerObject* player = this;
	bool oldplayingstate = player->playing;

	if(oldplayingstate != playing)
		outOfSync = true;

	PyScopedGIL gil;
	{
		PyScopedGIUnlock gunlock;
		
		if(playing)
			startWorkerThread(); // if not running yet, start
		
		if(playing && !openOutStream())
			playing = false;
		
		if(soundcardOutputEnabled && player->outStream.get() && player->outStream->isOpen() && oldplayingstate != playing)
			fader.change(playing ? 1 : -1, outSamplerate);
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

void PlayerObject::resetPlaying() {
	if(this->playing)
		this->setPlaying(false);
	if(this->outStream.get() != NULL)
		this->outStream.reset();
	reinitPlayerOutput();
}


std::string PlayerObject::getSoundDevice() {
	if(outStream.get() != NULL)
		return outStream->soundDevice;
	PaDeviceIndex idx = PlayerObject::OutStream::selectSoundDevice(preferredSoundDevice);
	if(idx >= 0)
		return Pa_GetDeviceInfo(idx)->name;
	return "";
}


#ifdef __APPLE__
// https://developer.apple.com/library/mac/#documentation/Darwin/Conceptual/KernelProgramming/scheduler/scheduler.html
// Also, from Google Native Client, osx/nacl_thread_nice.c has some related code.
// Or, from Google Chrome, platform_thread_mac.mm. http://src.chromium.org/svn/trunk/src/base/threading/platform_thread_mac.mm
void setRealtime(double dutyCicleMs) {
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
	
	// Get the conversion factor from milliseconds to absolute time
	// which is what the time-constraints call needs.
	mach_timebase_info_data_t tb_info;
	mach_timebase_info(&tb_info);
	double timeFact = ((double)tb_info.denom / (double)tb_info.numer) * 1000000;
	
	// In Chrome: period = 2.9ms ~= 128 frames @44.1KHz, comp = 0.75 * period, constr = 0.85 * period.
	// Also read: http://lists.apple.com/archives/coreaudio-api/2009/Jun/msg00059.html
	// Or: http://web.archiveorange.com/archive/v/q7bubBVFSGH286ErO0zz
	thread_time_constraint_policy_data_t ttcpolicy;
	ttcpolicy.period = dutyCicleMs * timeFact;
	ttcpolicy.computation = dutyCicleMs * 0.75 * timeFact;
	ttcpolicy.constraint = dutyCicleMs * 0.85 * timeFact;
	ttcpolicy.preemptible = 0;
	
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
void setRealtime(double dutyCicleMs) {} // not implemented yet
#endif





PyObject* pyGetSoundDevices(PyObject* self) {
	int num = Pa_GetDeviceCount();
	std::vector<const PaDeviceInfo*> devs;
	devs.reserve(num);
	for(int i = 0; i < num; ++i) {
		const PaDeviceInfo* info = Pa_GetDeviceInfo(i);
		if(info->maxOutputChannels > 0)
			devs.push_back(info);
	}
	
	PyObject* l = PyList_New(devs.size());
	if(!l) return NULL;
	
	for(int i = 0; i < (int)devs.size(); ++i) {
		const PaDeviceInfo* info = devs[i];
		PyObject* s = PyString_FromString(info->name);
		if(!s) {
			Py_DECREF(l);
			return NULL;
		}
		PyList_SET_ITEM(l, i, s);
	}
	
	return l;
}

