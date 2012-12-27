// Python module for playing audio
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#ifndef MusicPlayer_ffmpeg_h
#define MusicPlayer_ffmpeg_h

// Import Python first. This will define _GNU_SOURCE. This is needed to get strdup (and maybe others). We could also define _GNU_SOURCE ourself, but pyconfig.h from Python has troubles then and redeclares some other stuff. So, to just import Python first is the simplest way.
#include <Python.h>
#include <pythread.h>

#include <stddef.h>
#include <assert.h>

/* Some confusion about Python functions and their reference counting:
 
 PyObject_GetAttrString: returns new reference!
 PyDict_SetItem: increments reference on key and value!
 PyDict_SetItemString: increments reference on value!
 PyDict_GetItemString: does not inc ref of returned obj, i.e. borrowed ref! (unlike PyObject_GetAttrString)
 PyTuple_Pack: increments references on passed objects
 PyTuple_SetItem: does *not* increment references, i.e. steals ref (unlike PyDict_SetItem)
 PyList_Append: inc ref of passed object
 PyList_SetItem: does *not* inc ref on obj!
 */

#ifdef __cplusplus
extern "C" {
#endif

int PyDict_SetItemString_retain(PyObject* dict, const char* key, PyObject* value);

// this is mostly safe to call.
// returns a newly allocated c-string.
char* objStrDup(PyObject* obj);

// returns a newly allocated c-string.
char* objAttrStrDup(PyObject* obj, const char* attrStr);

int initPlayerDecoder();
int initPlayerOutput();

extern PyTypeObject Player_Type;

PyObject* pyCreatePlayer(PyObject* self);
PyObject* pySetFfmpegLogLevel(PyObject* self, PyObject* args);
PyObject* pyGetMetadata(PyObject* self, PyObject* args);
PyObject* pyCalcAcoustIdFingerprint(PyObject* self, PyObject* args);
PyObject* pyCalcBitmapThumbnail(PyObject* self, PyObject* args, PyObject* kws);
PyObject* pyCalcReplayGain(PyObject* self, PyObject* args, PyObject* kws);

#ifdef __cplusplus
}

struct PyMutex {
	PyThread_type_lock l;
	PyMutex(); ~PyMutex();
	void lock();
	bool lock_nowait();
	void unlock();
};

struct PyScopedLock {
	PyMutex& mutex;
	PyScopedLock(PyMutex& m);
	~PyScopedLock();
};

struct PyScopedUnlock {
	PyMutex& mutex;
	PyScopedUnlock(PyMutex& m);
	~PyScopedUnlock();
};


#include <boost/function.hpp>

struct PyThread {
	PyMutex lock;
	bool running;
	bool stopSignal;
	boost::function<void(PyMutex& lock, bool& stopSignal)> func;
	long ident;
	PyThread(); ~PyThread();
	bool start();
	void wait();
	void stop();
};

#include <boost/shared_ptr.hpp>
#include <list>

#define BUFFER_CHUNK_SIZE (1024 * 4)

struct Buffer {
	struct Chunk {
		uint8_t data[BUFFER_CHUNK_SIZE];
		uint16_t start, end;
		uint8_t* pt() { return data + start; }
		uint16_t size() const { assert(start <= end); return end - start; }
		static uint16_t BufferSize() { return BUFFER_CHUNK_SIZE; }
		uint16_t freeDataAvailable() { return BufferSize() - end; }
		Chunk() : start(0), end(0) {}
	};
	std::list<Chunk> chunks;
	
	size_t size() const;
	void clear() { chunks.clear(); }
	bool empty();
	
	// returns amount of data returned, i.e. <= target_size
	size_t pop(uint8_t* target, size_t target_size);
	
	void push(const uint8_t* data, size_t size);
};

// see smoothClip()
struct SmoothClipCalc {
	float x1, x2;
	double a,b,c,d;
	void setX(float x1, float x2);
	double get(double x);
};

// The player structure. Create by ffmpeg.createPlayer().
// This struct is initialized in player_init().
struct PlayerObject {
	PyObject_HEAD
	
	// public
	PyObject* queue;
	PyObject* curSong;
	bool playing;
	int setPlaying(bool playing);
	float volume;
	SmoothClipCalc volumeSmoothClip; // see smoothClip()
	bool volumeAdjustNeeded() const;
	int outSamplerate;
	int outNumChannels;
	void setAudioTgt(int samplerate, int numchannels);
	double timeDelay(size_t sampleNum) { return double(sampleNum)/outSamplerate/outNumChannels; }
	
	// private
	PyObject* dict;

	bool nextSongOnEof;
	bool skipPyExceptions; // for all callbacks, mainly song.readPacket
	bool needRealtimeReset; // PortAudio callback thread must set itself to realtime
	
	int seekRel(double incr);
	int seekAbs(double pos);
	bool getNextSong(bool skipped);
	
	void workerProc(PyMutex& lock, bool& stopSignal);
	PyThread workerThread;
	
	struct InStream;
	boost::shared_ptr<InStream> inStream;
	bool openInStream();
	bool isInStreamOpened() const; // in case we hit EOF, it is still opened
	Buffer* inStreamBuffer();
	void resetBuffers();
	bool buffersFullEnough() const;
	bool processInStream(); // returns true if there was no error
	PyObject* curSongMetadata();
	double curSongPos();
	double curSongLen();
	float curSongGainFactor();
	
	// returns the data read by the inStream. no matter what, it will fill the requested samples, though (with silence if nothing else is possible).
	// the outStream will call this. data read here is supposed to go without delay to the soundcard. it will update the timePos.
	// it is supposed to be fast. if no data is available, it will not wait for it but it will fill silence.
	// this returns the internal format, i.e. SINT16, outSamplerate and outNumChannels.
	// it might also issue the callbacks like song finished, or proceed to the next song - but it wont call them itself (for performance reasons).
	bool readOutStream(int16_t* samples, size_t sampleNum);
	
	struct OutStream;
	boost::shared_ptr<OutStream> outStream;
		
	/* Important note about the lock:
	 To avoid deadlocks with on thread waiting on the Python GIL and another on this lock,
	 we must ensure a strict order in which we might acquire both locks:
	 When we acquire this/players lock, the PyGIL *must not* be held.
	 When we held this/players lock, the PyGIL can be acquired.
	 In practice, if we want this lock, if we hold already the PyGIL, we usually use this code:
	 Py_INCREF(player); // to assure that we have a real own ref
	 Py_BEGIN_ALLOW_THREADS
	 PyThread_acquire_lock(player->lock, WAIT_LOCK);
	 // do something (note that we dont hold the PyGIL here!)
	 PyThread_release_lock(player->lock);
	 Py_END_ALLOW_THREADS
	 Py_DECREF(player);
	 If we hold this lock and we also want to get the PyGIL, we use
	 PyGILState_Ensure()/PyGILState_Release() as usual.
	 We use this order because in the PaStream handling thread, we might just want to get
	 the players lock but don't always need the PyGIL.
	 */
	PyMutex lock;
		
};

#endif

#endif
