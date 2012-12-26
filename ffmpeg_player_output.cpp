// ffmpeg player output (portaudio)
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"

#include <portaudio.h>


int initPlayerOutput() {
	PaError ret = Pa_Initialize();
	if(ret != paNoError)
		Py_FatalError("PortAudio init failed");
	return 0;
}

static void player_closeOutputStream(PlayerObject* player) {
	// we expect that we have the lock here.
	// we must release the lock so that any thread-join can be done.
	PaStream* stream = player->outStream;
	player->outStream = NULL;
	PyThread_release_lock(player->lock);
	Pa_CloseStream(stream);
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
}

static void player_stopOutputStream(PlayerObject* player) {
	// we expect that we have the lock here.
	// we must release the lock so that any thread-join can be done.
	PaStream* stream = player->outStream;
	PyThread_release_lock(player->lock);
	Pa_StopStream(stream);
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
}






static
int paStreamCallback(
					 const void *input, void *output,
					 unsigned long frameCount,
					 const PaStreamCallbackTimeInfo* timeInfo,
					 PaStreamCallbackFlags statusFlags,
					 void *userData )
{
	PlayerObject* player = (PlayerObject*) userData;
	
	if(player->needRealtimeReset) {
		player->needRealtimeReset = 0;
		setRealtime();
	}

	player_fillOutStream(player, (uint8_t*) output, frameCount * 2 /* bytes */ * NUMCHANNELS);
	return paContinue;
}


static int player_setplaying(PlayerObject* player, int playing) {
	int oldplayingstate = 0;
	Py_INCREF((PyObject*)player);
	Py_BEGIN_ALLOW_THREADS
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
	if(playing && !player->outStream) {
		PaError ret;
		ret = Pa_OpenDefaultStream(
								   &player->outStream,
								   0,
								   player->audio_tgt.channels, // numOutputChannels
								   paInt16, // sampleFormat
								   player->audio_tgt.freq, // sampleRate
								   AUDIO_BUFFER_SIZE / 2, // framesPerBuffer,
								   &paStreamCallback,
								   player //void *userData
								   );
		if(ret != paNoError) {
			PyErr_SetString(PyExc_RuntimeError, "Pa_OpenDefaultStream failed");
			if(player->outStream)
				player_closeOutputStream(player);
			playing = 0;
		}
	}
	if(playing) {
		player->needRealtimeReset = 1;
		Pa_StartStream(player->outStream);
	} else
		player_stopOutputStream(player);
	oldplayingstate = player->playing;
	player->playing = playing;
	PyThread_release_lock(player->lock);
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



