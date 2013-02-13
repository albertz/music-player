// ffmpeg_replaygain.cpp
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"

// Note: The yule/butter tables below have hardcoded values for this samplerate.
#define SAMPLERATE 44100
#define NUMCHANNELS 2

// http://www.replaygain.org/

#define YULE_ORDER 10
#define BUTTER_ORDER 2
#define MAX_FILTER_ORDER 10
#define RMS_WINDOW_TIME 0.050 // ReplayGain spec standard
#define MAX_SAMPLES_PER_WINDOW  (size_t) (SAMPLERATE * RMS_WINDOW_TIME) // ReplayGain spec standard
#define REPLAYGAIN_LOUD_PERC 0.95 // ReplayGain spec standard
#define RG_STEPS_per_dB      100.    // loudness table entries per dB
#define RG_MAX_dB            120.    // loudness table entries for 0...MAX_dB (normal max. values are 70...80 dB)
#define RG_PINK_REF          64.82

typedef struct ReplayGainBuffersPerChannelStage {
	float data[MAX_SAMPLES_PER_WINDOW + MAX_FILTER_ORDER];
} ReplayGainBuffersPerChannelStage;

typedef struct ReplayGainBuffersPerChannel {
#define NUM_REPLAYGAIN_STAGES 3
	ReplayGainBuffersPerChannelStage stages[NUM_REPLAYGAIN_STAGES]; // in, step, out
} ReplayGainBuffersPerChannel;

typedef struct ReplayGainBuffer {
	ReplayGainBuffersPerChannel channels[NUMCHANNELS];
	uint32_t loudnessTable[(size_t)(RG_STEPS_per_dB * RG_MAX_dB)];
} ReplayGainBuffer;

static void _genericFilter(float* out, const float* in, const float* kernel, int order) {
	*out = in[0] * kernel[0];
	for(int i = 1; i <= order; ++i) {
		*out -= out[-i] * kernel[i*2 - 1];
		*out += in[-i] * kernel[i*2];
	}
}

static void yuleFilter(float* out, float* in) {
	static const float YuleCoeff[] = {0.05418656406430, -3.47845948550071, -0.02911007808948,  6.36317777566148, -0.00848709379851, -8.54751527471874, -0.00851165645469,  9.47693607801280, -0.00834990904936, -8.81498681370155,  0.02245293253339,  6.85401540936998, -0.02596338512915, -4.39470996079559,  0.01624864962975,  2.19611684890774, -0.00240879051584, -0.75104302451432,  0.00674613682247,  0.13149317958808, -0.00187763777362 };
	assert(sizeof(YuleCoeff)/sizeof(YuleCoeff[0]) == YULE_ORDER*2 + 1);
	_genericFilter(out, in, YuleCoeff, YULE_ORDER);
}

static void butterFilter(float* out, float* in) {
	static const float ButterCoeff[] = {0.98500175787242, -1.96977855582618, -1.97000351574484,  0.97022847566350,  0.98500175787242 };
	assert(sizeof(ButterCoeff)/sizeof(ButterCoeff[0]) == BUTTER_ORDER*2 + 1);
	_genericFilter(out, in, ButterCoeff, BUTTER_ORDER);
}

static double replayGainHandleWindow(ReplayGainBuffer* buffer) {
	double sum = 0;
	for(int chan = 0; chan < NUMCHANNELS; ++chan) {
		for(size_t samplePos = 0; samplePos < MAX_SAMPLES_PER_WINDOW; ++samplePos) {
			float* d0 = buffer->channels[chan].stages[0].data + MAX_FILTER_ORDER + samplePos;
			float* d1 = buffer->channels[chan].stages[1].data + MAX_FILTER_ORDER + samplePos;
			float* d2 = buffer->channels[chan].stages[2].data + MAX_FILTER_ORDER + samplePos;
			
			yuleFilter(d1, d0);
			*d1 += 1e-10; // hack from original implementation: to avoid slowdown because of denormals
			butterFilter(d2, d1);
			sum += *d2 * *d2;
		}
	}
	
	double decibel = 10 * log10(sum / (NUMCHANNELS * MAX_SAMPLES_PER_WINDOW) + 1e-37);
	
	int i = RG_STEPS_per_dB * decibel;
	if(i < 0) i = 0;
	if(i >= sizeof(buffer->loudnessTable)/sizeof(buffer->loudnessTable[0]))
		i = sizeof(buffer->loudnessTable)/sizeof(buffer->loudnessTable[0]) - 1;
	buffer->loudnessTable[i]++;
	
	return decibel;
}

PyObject *
pyCalcReplayGain(PyObject* self, PyObject* args, PyObject* kws) {
	PyObject* songObj = NULL;
	static const char *kwlist[] = {
		"song",
		NULL};
	if(!PyArg_ParseTupleAndKeywords(
			args, kws, "O:calcReplayGain", (char**)kwlist,
			&songObj
			))
		return NULL;
	
	PyObject* returnObj = NULL;
	PlayerObject* player = NULL;
	ReplayGainBuffer* buffer = NULL;
	unsigned long totalFrameCount = 0;
	size_t samplePos = 0;
	size_t windowCount = 0;
	
	player = (PlayerObject*) pyCreatePlayer(NULL);
	if(!player) goto final;
	player->lock.enabled = false;
	player->setAudioTgt(SAMPLERATE, NUMCHANNELS);
	player->nextSongOnEof = 0;
	player->skipPyExceptions = 0;
	player->playing = true; // otherwise audio_decode_frame() wont read
	player->volume = 1; player->volumeSmoothClip.setX(1, 1); // avoid volume adjustments
	assert(!player->volumeAdjustNeeded());
	Py_INCREF(songObj);
	player->curSong = songObj;
	if(PyObject_HasAttrString(songObj, "gain"))
		printf("pyCalcReplayGain: warning: song has gain already - this will lead to wrong gain calculation\n");
	if(!player->openInStream()) goto final;
	if(PyErr_Occurred()) goto final;
	if(!player->isInStreamOpened()) goto final;
	
	buffer = (ReplayGainBuffer*)malloc(sizeof(ReplayGainBuffer));
	memset(buffer, 0, sizeof(ReplayGainBuffer));
	
	while (player->processInStream()) {
		if(PyErr_Occurred()) goto final;
		for(auto& it : player->inStreamBuffer()->chunks) {		
			totalFrameCount += it.size() / NUMCHANNELS / 2 /* S16 */;
			
			short channel = 0;
			for(size_t i = 0; i < it.size() / 2; ++i) {
				int16_t* sampleAddr = (int16_t*) it.pt() + i;
				int16_t sample = *sampleAddr; // TODO: endian swap?
				// It is by purpose that we don't normalize to [-1,1] but stay in the range [-0x8000,0x7fff].
				// That is because it was originially based on CD data, which is 16-bit signed integers.
				float sampleFloat = sample;
				
				buffer->channels[channel].stages[0].data[samplePos + MAX_FILTER_ORDER] = sampleFloat;
				
				++channel;
				if(channel >= NUMCHANNELS) {
					channel = 0;
					++samplePos;
					if(samplePos >= MAX_SAMPLES_PER_WINDOW) {
						// buffer is full. i.e. we have a full window. handle it.
						replayGainHandleWindow(buffer);
						++windowCount;
						
						// move on now.
						for(int chan = 0; chan < NUMCHANNELS; ++chan)
							for(int stage = 0; stage < NUM_REPLAYGAIN_STAGES; ++stage)
								memcpy(
									   buffer->channels[chan].stages[stage].data,
									   buffer->channels[chan].stages[stage].data + MAX_SAMPLES_PER_WINDOW,
									   MAX_FILTER_ORDER * sizeof(buffer->channels[0].stages[0].data[0]));
						samplePos = 0;
					}
				}
			}
		}
		player->inStreamBuffer()->clear();
	}
	{
		double songDuration = (double)totalFrameCount / SAMPLERATE;
		
		float gain = 0;
		int64_t upperLoudness = (int64_t) ceil(windowCount * (1.0 - REPLAYGAIN_LOUD_PERC));
		for(int i = sizeof(buffer->loudnessTable)/sizeof(buffer->loudnessTable[0]) - 1; i >= 0; --i) {
			upperLoudness -= buffer->loudnessTable[i];
			if(upperLoudness <= 0) {
				gain = RG_PINK_REF - (float)i / RG_STEPS_per_dB;
				break;
			}
		}
		
		returnObj = PyTuple_New(2);
		PyTuple_SetItem(returnObj, 0, PyFloat_FromDouble(songDuration));
		PyTuple_SetItem(returnObj, 1, PyFloat_FromDouble(gain));
	}

final:
	if(buffer) free(buffer);
	if(!PyErr_Occurred() && !returnObj) {
		returnObj = Py_None;
		Py_INCREF(returnObj);
	}
	Py_XDECREF(player);
	return returnObj;
}
