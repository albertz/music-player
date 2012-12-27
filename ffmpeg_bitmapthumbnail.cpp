// ffmpeg_bitmapthumbnail.cpp
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"

#include <libavformat/avformat.h>
#include <libavcodec/avfft.h>



// note that each row in imgDataStart is aligned to 4 bytes
#define ALIGN4(n) ((n)+3 - ((n)+3) % 4)
// each single pixel is decoded as BGR
static
PyObject* createBitmap24Bpp(int w, int h, char** imgDataStart) {
	assert(imgDataStart);
	
	// http://en.wikipedia.org/wiki/BMP_file_format
	
	static const int FileHeaderSize = 14;
	static const int InfoHeaderSize = 40; // format BITMAPINFOHEADER
	size_t bmpSize = FileHeaderSize + InfoHeaderSize + ALIGN4(3 * w) * h;
	PyObject* bmp = PyString_FromStringAndSize(NULL, bmpSize);
	if(!bmp) return NULL;
	memset(PyString_AS_STRING(bmp), 0, bmpSize);
	
	unsigned char* bmpfileheader = (unsigned char*) PyString_AS_STRING(bmp);
	unsigned char* bmpinfoheader = bmpfileheader + FileHeaderSize;
	*imgDataStart = (char*) bmpinfoheader + InfoHeaderSize;
	
	// header field
	bmpfileheader[ 0] = 'B';
	bmpfileheader[ 1] = 'M';
	
	bmpfileheader[ 2] = (unsigned char)(bmpSize    );
	bmpfileheader[ 3] = (unsigned char)(bmpSize>> 8);
	bmpfileheader[ 4] = (unsigned char)(bmpSize>>16);
	bmpfileheader[ 5] = (unsigned char)(bmpSize>>24);
	
	assert(FileHeaderSize + InfoHeaderSize < 256);
	bmpfileheader[10] = FileHeaderSize + InfoHeaderSize; // starting address of image data (32bit)
	
	bmpinfoheader[ 0] = InfoHeaderSize; // size of info header. (32bit)
	
	bmpinfoheader[ 4] = (unsigned char)(w    );
	bmpinfoheader[ 5] = (unsigned char)(w>> 8);
	bmpinfoheader[ 6] = (unsigned char)(w>>16);
	bmpinfoheader[ 7] = (unsigned char)(w>>24);
	bmpinfoheader[ 8] = (unsigned char)(h    );
	bmpinfoheader[ 9] = (unsigned char)(h>> 8);
	bmpinfoheader[10] = (unsigned char)(h>>16);
	bmpinfoheader[11] = (unsigned char)(h>>24);
	
	bmpinfoheader[12] = 1; // num of color planes. must be 1 (16bit)
	bmpinfoheader[14] = 24; // bpp (16bit)
	
	return bmp;
}

static
void bmpSetPixel(char* img, int w, int x, int y, unsigned char r, unsigned char g, unsigned char b) {
	img[y * ALIGN4(3 * w) + x * 3 + 0] = (char) b;
	img[y * ALIGN4(3 * w) + x * 3 + 1] = (char) g;
	img[y * ALIGN4(3 * w) + x * 3 + 2] = (char) r;
}


// f must be in [0,1]
static
void rainbowColor(float f, unsigned char* r, unsigned char* g, unsigned char* b) {
	if(f < 0.0) {
		*r = 255;
		*g = 0;
		*b = 0;
	}
	else if(f < 1.0/6) {
		f *= 6;
		*r = 255;
		*g = 255 * f;
		*b = 0;
	}
	else if(f < 2.0/6) {
		f = f * 6 + 1;
		*r = 255 * (1 - f);
		*g = 255;
		*b = 0;
	}
	else if(f < 3.0/6) {
		f = f * 6 + 2;
		*r = 0;
		*g = 255;
		*b = 255 * f;
	}
	else if(f < 4.0/6) {
		f = f * 6 + 3;
		*r = 0;
		*g = 255 * (1 - f);
		*b = 255;
	}
	else if(f < 5.0/6) {
		f = f * 6 + 4;
		*r = 255 * f;
		*g = 0;
		*b = 255;
	}
	else if(f < 6.0/6) {
		f = f * 6 + 5;
		*r = 255;
		*g = 0;
		*b = 255 * (1 - f);
	}
	else {
		*r = 255;
		*g = 0;
		*b = 0;
	}
}


// idea loosely from:
// http://www.freesound.org/
// https://github.com/endolith/freesound-thumbnailer/blob/master/processing.py

PyObject *
pyCalcBitmapThumbnail(PyObject* self, PyObject* args, PyObject* kws) {
	PyObject* songObj = NULL;
	int bmpWidth = 400, bmpHeight = 101;
	unsigned char bgR = 100, bgG = bgR, bgB = bgR;
	unsigned char timeR = 170, timeG = timeR, timeB = timeR;
	int timelineSecInterval = 10;
	PyObject* procCallback = NULL;
	float volume = 1; // better default value here. note that we also do gain handling if it is set
	float volumeSmoothClipX1 = 0.95, volumeSmoothClipX2 = 10;
	static const char *kwlist[] = {
		"song", "width", "height",
		"backgroundColor", "timelineColor",
		"timelineSecInterval",
		"procCallback",
		"volume",
		"volumeSmootClip",
		NULL};
	if(!PyArg_ParseTupleAndKeywords(args, kws, "O|ii(bbb)(bbb)iOf(ff):calcBitmapThumbnail", (char**)kwlist,
									&songObj,
									&bmpWidth, &bmpHeight,
									&bgR, &bgG, &bgB,
									&timeR, &timeG, &timeB,
									&timelineSecInterval,
									&procCallback,
									&volume, &volumeSmoothClipX1, &volumeSmoothClipX2))
		return NULL;
	
	char* img = NULL;
	PyObject* bmp = createBitmap24Bpp(bmpWidth, bmpHeight, &img);
	if(!bmp)
		return NULL; // out of memory
	
	RDFTContext* fftCtx = NULL;
	float* samplesBuf = NULL;
	PyObject* returnObj = NULL;
	PlayerObject* player = NULL;
	unsigned long totalFrameCount = 0;
	double songDuration = 0;
	double samplesPerPixel = 0;
	unsigned long frame = 0;
	
	player = (PlayerObject*) pyCreatePlayer(NULL);
	if(!player) goto final;
	player->nextSongOnEof = 0;
	player->skipPyExceptions = 0;
	player->volume = volume;
	player->volumeSmoothClip.setX(volumeSmoothClipX1, volumeSmoothClipX2);
	player->playing = 1; // otherwise audio_decode_frame() wont read
	Py_INCREF(songObj);
	player->curSong = songObj;
	if(!player->openInStream()) goto final;
	if(player->inStream == NULL) goto final;
	
	// First count totalFrameCount.
	while(player->processInStream()) {
		if(PyErr_Occurred()) goto final;
		
		totalFrameCount += player->inStreamBuffer()->size() / player->outNumChannels / 2 /* S16 */;
		player->inStreamBuffer()->clear();
	}
	songDuration = (double)totalFrameCount / player->outSamplerate;
	
	// Seek back.
	player->seekAbs(0.0);
	if(PyErr_Occurred()) goto final;
	
	// init the processor
#define fftSizeLog2 (11)
#define fftSize (1 << fftSizeLog2)
	float freqWindow[fftSize];
	for(int i = 0; i < fftSize; ++i)
		// Hanning window
		freqWindow[i] = (float) (0.5 * (1.0 - cos((2.0 * M_PI * i) / (fftSize - 1))));
	fftCtx = av_rdft_init(fftSizeLog2, DFT_R2C);
	if(!fftCtx) {
		printf("ERROR: av_rdft_init failed\n");
		goto final;
	}
	// Note: We have to use av_mallocz here to have the right mem alignment.
	// That is also why we can't allocate it on the stack (without doing alignment).
	samplesBuf = (float *)av_mallocz(sizeof(float) * fftSize);
	
	samplesPerPixel = totalFrameCount / (double)bmpWidth;
	
	for(int x = 0; x < bmpWidth; ++x) {
		
		// draw background
		for(int y = 0; y < bmpHeight; ++y)
			bmpSetPixel(img, bmpWidth, x, y, bgR, bgG, bgB);
		
		// call the callback every 60 secs
		if(procCallback && (int)(songDuration * x / bmpWidth / 60) < (int)(songDuration * (x+1) / bmpWidth / 60)) {
			PyGILState_STATE gstate = PyGILState_Ensure();
			
			Py_INCREF(bmp);
			Py_INCREF(songObj);
			PyObject* args = PyTuple_New(4);
			PyTuple_SetItem(args, 0, songObj);
			PyTuple_SetItem(args, 1, PyFloat_FromDouble((double) x / bmpWidth));
			PyTuple_SetItem(args, 2, PyFloat_FromDouble(songDuration));
			PyTuple_SetItem(args, 3, bmp);
			PyObject* retObj = PyObject_CallObject(procCallback, args);
			int stop = 0;
			if(PyErr_Occurred()) {
				PyErr_Print();
				procCallback = NULL; // don't call again
				stop = 1; // just break the whole thing
			}
			else if(retObj)
				stop = !PyObject_IsTrue(retObj);
			else // retObj == NULL, strange, should be error
				stop = 1;
			Py_XDECREF(retObj);
			Py_DECREF(args); // this also decrefs song and bmp
			
			if(stop) {
				Py_DECREF(bmp);
				bmp = NULL;
			}
			
			PyGILState_Release(gstate);
			
			if(stop) goto final;
		}
		
		if((int)(songDuration * x / bmpWidth / timelineSecInterval) < (int)(songDuration * (x+1) / bmpWidth / timelineSecInterval)) {
			// draw timeline
			for(int y = 0; y < bmpHeight; ++y)
				bmpSetPixel(img, bmpWidth, x, y, timeR, timeG, timeB);
		}
		
		int samplesBufIndex = 0;
		memset(samplesBuf, 0, sizeof(float) * fftSize);
		
		float peakMin = 0, peakMax = 0;
		while(frame < (x + 1) * samplesPerPixel) {
			if(!player->processInStream())
				break; // probably EOF or so
			if(PyErr_Occurred()) goto final;
			
			for(auto& it : player->inStreamBuffer()->chunks) {
				for(size_t i = 0; i < it.size() / 2; ++i) {
					int16_t* sampleAddr = (int16_t*) it.pt() + i;
					int16_t sample = *sampleAddr; // TODO: endian swap?
					float sampleFloat = sample / ((double) 0x8000);
					
					if(sampleFloat < peakMin) peakMin = sampleFloat;
					if(sampleFloat > peakMax) peakMax = sampleFloat;
					
					if(samplesBufIndex < fftSize) {
						samplesBuf[samplesBufIndex] += sampleFloat * freqWindow[samplesBufIndex] * 0.5f /* we do this twice for each channel */;
					}
					if(i % 2 == 1) samplesBufIndex++;
				}
				
				frame += it.size() / player->outNumChannels / 2 /* S16 */;
			}
			player->inStreamBuffer()->clear();
		}
		
		av_rdft_calc(fftCtx, samplesBuf);
		
		float absFftData[fftSize / 2 + 1];
		float *in_ptr = samplesBuf;
		float *out_ptr = absFftData;
		out_ptr[0] = in_ptr[0] * in_ptr[0];
		out_ptr[fftSize / 2] = in_ptr[1] * in_ptr[1];
		out_ptr += 1;
		in_ptr += 2;
		for(int i = 1; i < fftSize / 2; i++) {
			*out_ptr++ = in_ptr[0] * in_ptr[0] + in_ptr[1] * in_ptr[1];
			in_ptr += 2;
		}
		
		float energy = 0;
		for(int i = 0; i < fftSize / 2; ++i)
			energy += absFftData[i];
		
		// compute the spectral centroid in hertz
		float spectralCentroid = 0;
		for(int i = 0; i < fftSize / 2; ++i)
			spectralCentroid += absFftData[i] * i;
		spectralCentroid /= energy;
		spectralCentroid /= fftSize / 2;
		spectralCentroid *= player->outSamplerate;
		spectralCentroid *= 0.5;
		
		// clip
		static const float lowerFreq = 100;
		static const float higherFreq = 22050;
		if(spectralCentroid < lowerFreq) spectralCentroid = lowerFreq;
		if(spectralCentroid > higherFreq) spectralCentroid = higherFreq;
		
		// apply log so it's proportional to human perception of frequency
		spectralCentroid = log10(spectralCentroid);
		
		// scale to [0,1]
		spectralCentroid -= log10(lowerFreq);
		spectralCentroid /= (log10(higherFreq) - log10(lowerFreq));
		
		//printf("x %i, peak %f,%f, spec %f\n", x, peakMin, peakMax, spectralCentroid);
		
		// get color from spectralCentroid
		unsigned char r = 0, g = 0, b = 0;
		rainbowColor(spectralCentroid, &r, &g, &b);
		
		int y1 = bmpHeight * 0.5 + peakMin * (bmpHeight - 4) * 0.5;
		int y2 = bmpHeight * 0.5 + peakMax * (bmpHeight - 4) * 0.5;
		if(y1 < 0) y1 = 0;
		if(y2 >= bmpHeight) y2 = bmpHeight - 1;
		
		// draw line
		for(int y = y1; y <= y2; ++y)
			bmpSetPixel(img, bmpWidth, x, y, r, g, b);
	}
	
	// We have to hold the Python GIL for this block
	// because of the callback, other Python code/threads
	// might have references to bmp.
	{
		PyGILState_STATE gstate = PyGILState_Ensure();
		
		returnObj = PyTuple_New(2);
		PyTuple_SetItem(returnObj, 0, PyFloat_FromDouble(songDuration));
		PyTuple_SetItem(returnObj, 1, bmp);
		bmp = NULL; // returnObj has taken over the reference
		
		PyGILState_Release(gstate);
	}
	
final:
	Py_XDECREF(bmp); // this is multithreading safe in all cases where bmp != NULL
	if(fftCtx)
		av_rdft_end(fftCtx);
	if(samplesBuf)
		av_free(samplesBuf);
	if(!PyErr_Occurred() && !returnObj) {
		returnObj = Py_None;
		Py_INCREF(returnObj);
	}
	Py_XDECREF(player);
	return returnObj;
}

