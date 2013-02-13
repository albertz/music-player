// ffmpeg_acoustid.cpp
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"
#include <chromaprint.h>

PyObject *
pyCalcAcoustIdFingerprint(PyObject* self, PyObject* args) {
	PyObject* songObj = NULL;
	if(!PyArg_ParseTuple(args, "O:calcAcoustIdFingerprint", &songObj))
		return NULL;
	
	PyObject* returnObj = NULL;
	PlayerObject* player = NULL;
	ChromaprintContext *chromaprint_ctx = NULL;
	unsigned long totalFrameCount = 0;
	
	player = (PlayerObject*) pyCreatePlayer(NULL);
	if(!player) goto final;
	player->lock.enabled = false;
	player->nextSongOnEof = 0;
	player->skipPyExceptions = 0;
	player->playing = 1; // otherwise audio_decode_frame() wont read
	player->volume = 1; player->volumeSmoothClip.setX(1, 1); // avoid volume adjustments
	Py_INCREF(songObj);
	player->curSong = songObj;
	if(!player->openInStream()) goto final;
	if(PyErr_Occurred()) goto final;
	if(player->inStream == NULL) goto final;
	
	// fpcalc source for reference:
	// https://github.com/lalinsky/chromaprint/blob/master/examples/fpcalc.c
	
	chromaprint_ctx = chromaprint_new(CHROMAPRINT_ALGORITHM_DEFAULT);
	chromaprint_start(chromaprint_ctx, player->outSamplerate, player->outNumChannels);
	
	// Note that we don't have any max_length handling yet.
	// fpcalc uses a default of 120 seconds.
	// This function right now doesn't rely on any external song duration
	// source, so it is a perfect reliable way to calculate also the
	// song duration.
	// I'm not sure how expensive audio_decode_frame is compared to
	// chromaprint_feed, so if we just decode everything to calculate
	// a reliable song duration, it might make sense to just feed
	// everything to chromaprint.
	// Maybe we can optimize audio_decode_frame though to just return the
	// len and don't do any decoding if we just want to calculate the len.
	// This is all open for future hacking ... But it works good enough now.
	
	while(player->processInStream()) {
		if(PyErr_Occurred()) goto final;
		for(auto& it : player->inStreamBuffer()->chunks) {
			totalFrameCount += it.size() / player->outNumChannels / 2 /* S16 */;
		
			if (!chromaprint_feed(chromaprint_ctx, it.pt(), it.size() / 2)) {
				fprintf(stderr, "ERROR: fingerprint feed calculation failed\n");
				goto final;
			}
		}
		player->inStreamBuffer()->clear();
	}
	{
		double songDuration = (double)totalFrameCount / player->outSamplerate;
		char* fingerprint = NULL;
		
		if (!chromaprint_finish(chromaprint_ctx)) {
			fprintf(stderr, "ERROR: fingerprint finish calculation failed\n");
			goto final;
		}

		if (!chromaprint_get_fingerprint(chromaprint_ctx, &fingerprint)) {
			fprintf(stderr, "ERROR: unable to calculate fingerprint, get_fingerprint failed\n");
			goto final;
		}
		
		returnObj = PyTuple_New(2);
		PyTuple_SetItem(returnObj, 0, PyFloat_FromDouble(songDuration));
		PyTuple_SetItem(returnObj, 1, PyString_FromString(fingerprint));
		
		chromaprint_dealloc(fingerprint);
	}
	
final:
	if(chromaprint_ctx)
		chromaprint_free(chromaprint_ctx);
	if(!PyErr_Occurred() && !returnObj) {
		returnObj = Py_None;
		Py_INCREF(returnObj);
	}
	Py_XDECREF(player);
	return returnObj;
}
