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
#include <stdint.h>
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
struct PlayerObject;

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

// this is defined in <sys/mman.h>. systems which don't have that should provide a dummy/wrapper
int mlock(const void *addr, size_t len);

#ifdef __cplusplus
}

#include <string>

std::string objAttrStr(PyObject* obj, const std::string& attrStr);

#include <boost/function.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/noncopyable.hpp>
#include <list>

struct PyMutex {
	PyThread_type_lock l;
	bool enabled;
	PyMutex(); ~PyMutex();
	PyMutex(const PyMutex&) : PyMutex() {} // ignore
	PyMutex& operator=(const PyMutex&) { return *this; } // ignore
	void lock();
	bool lock_nowait();
	void unlock();
};

struct PyScopedLock : boost::noncopyable {
	PyMutex& mutex;
	PyScopedLock(PyMutex& m);
	~PyScopedLock();
};

struct PyScopedUnlock : boost::noncopyable {
	PyMutex& mutex;
	PyScopedUnlock(PyMutex& m);
	~PyScopedUnlock();
};

struct PyScopedGIL : boost::noncopyable {
	PyGILState_STATE gstate;
	PyScopedGIL() { gstate = PyGILState_Ensure(); }
	~PyScopedGIL() { PyGILState_Release(gstate); }
};

struct PyScopedGIUnlock : boost::noncopyable {
	PyScopedGIL gstate; // in case we didn't had the GIL
	PyThreadState* _save;
	PyScopedGIUnlock() : _save(NULL) { Py_UNBLOCK_THREADS }
	~PyScopedGIUnlock() { Py_BLOCK_THREADS }
};

struct ProtectionData : boost::noncopyable {
	PyMutex mutex;
	uint16_t lockCounter;
	long lockThreadIdent;
	bool isValid;
	ProtectionData(); ~ProtectionData();
	void lock();
	void unlock();
};

typedef boost::shared_ptr<ProtectionData> ProtectionPtr;
struct Protection : boost::noncopyable {
	ProtectionPtr prot;
	Protection() : prot(new ProtectionData) {}
};

struct ProtectionScope : boost::noncopyable {
	ProtectionPtr prot;
	ProtectionScope(const Protection& p);
	~ProtectionScope();
	void setInvalid();
	bool isValid();
};


struct PyThread : boost::noncopyable {
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


#define BUFFER_CHUNK_SIZE (1024 * 4)

struct Buffer {
	PyMutex mutex;

	struct Chunk {
		uint8_t data[BUFFER_CHUNK_SIZE];
		uint16_t start, end;
		uint8_t* pt() { return data + start; }
		uint16_t size() const { assert(start <= end); return end - start; }
		static uint16_t BufferSize() { return BUFFER_CHUNK_SIZE; }
		uint16_t freeDataAvailable() { return BufferSize() - end; }
		Chunk() : start(0), end(0) { mlock(this, sizeof(*this)); }
	};
	std::list<Chunk> chunks;
	size_t _size;
	
	Buffer() : _size(0) { mlock(this, sizeof(*this)); }
	size_t size() { PyScopedLock lock(mutex); return _size; }
	void clear() { PyScopedLock lock(mutex); chunks.clear(); _size = 0; }
	bool empty() { return size() == 0; }
	
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

struct Fader {
	uint16_t cur;
	uint16_t limit;
	int8_t inc; // -1 or 1 or 0
	Fader();
	void init(int8_t inc /* 1 for fading in, -1 for fading out */, int Samplerate);
	void frameTick();
	void finish();
	bool finished();
	double sampleFactor();
	void wait(PlayerObject* player);
};


template<typename ValueT>
struct _Value {
	const ValueT value;
	_Value(const ValueT& _v) : value(_v) {}
	
	template<typename T=ValueT>
	T clamp(T lowerLimit, T upperLimit) {
		T res = value;
		if(res < lowerLimit) res = lowerLimit;
		if(res > upperLimit) res = upperLimit;
		return res;
	}
};
template<typename T> _Value<T> _makeValue(const T& v) { return _Value<T>(v); }

typedef float float32_t;
static_assert(sizeof(float32_t) == 4, "float32_t declaration is wrong");

#define _FloatToPCM_raw(sample) (sample * ((double) 0x8000))
#define _FloatToPCM_clampFloat(sample) \
	(_makeValue(sample).clamp<>(-1., 1.))
// guaranteed to be in right range of right type (int16_t)
#define FloatToPCM16(s) \
	((int16_t)_makeValue(_FloatToPCM_raw(_FloatToPCM_clampFloat(s))).clamp<int32_t>(-0x8000, 0x7fff))

#if defined(OUTSAMPLEFORMAT_INT16)
#define OUTSAMPLE_t int16_t
#define OUTSAMPLEFORMATSTR "int"
#define OUTSAMPLEBITLEN 16
// normed in [-1,1] range. not clamped
#define OutSampleAsFloat(sample) (((double) sample) / ((double) 0x8000))
// normed in [-0x8000,0x7fff]. not clamped
#define OutSampleAsInt(sample) sample
// guaranteed to be in right range of type OUTSAMPLE_t
#define FloatToOutSample(sample) FloatToPCM16(sample)

#else
#define OUTSAMPLE_t float32_t
#define OUTSAMPLEFORMATSTR "float"
#define OUTSAMPLEBITLEN 32
// normed in [-1,1] range. not clamped
#define OutSampleAsFloat(sample) (sample)
// normed in [-0x8000,0x7fff]. not clamped
#define OutSampleAsInt(sample) (sample * ((double) 0x8000))
// guaranteed to be in right range of type OUTSAMPLE_t
#define FloatToOutSample(sample) (_makeValue(sample).clamp<OUTSAMPLE_t>(-1., 1.))
#endif

#define OUTSAMPLEBYTELEN (OUTSAMPLEBITLEN / 8)

// The player structure. Create by ffmpeg.createPlayer().
// This struct is initialized in player_init().
struct PlayerObject {
	PyObject_HEAD
	
	// public
	PyObject* queue;
	PyObject* peekQueue;
	PyObject* curSong;
	bool playing;
	bool soundcardOutputEnabled; // if enabled, uses PortAudio to play on soundcard. otherwise call readStreamOut manually
	int setPlaying(bool playing);
	void resetPlaying();
	float volume;
	SmoothClipCalc volumeSmoothClip; // see smoothClip()
	bool volumeAdjustEnabled;
	bool volumeAdjustNeeded() const;
	int outSamplerate;
	int outNumChannels;
	void setAudioTgt(int samplerate, int numchannels);
	double timeDelay(size_t sampleNum) { return double(sampleNum)/outSamplerate/outNumChannels; }
	Fader fader;
	
	// private
	PyObject* dict;

	bool nextSongOnEof;
	bool skipPyExceptions; // for all callbacks, mainly song.readPacket
	
	int seekRel(double incr);
	int seekAbs(double pos);
	bool getNextSong(bool skipped);
	
	void workerProc(PyMutex& lock, bool& stopSignal);
	PyThread workerThread;
	
	struct InStream;
	boost::shared_ptr<InStream> inStream;
	typedef std::list<boost::shared_ptr<InStream> > PeekInStreams;
	PeekInStreams peekInStreams;
	bool openInStream();
	bool tryOvertakePeekInStream();
	void openPeekInStreams();
	bool isInStreamOpened() const; // in case we hit EOF, it is still opened
	Buffer* inStreamBuffer();
	void resetBuffers();
	bool processInStream(); // returns true if there was no error
	PyObject* curSongMetadata();
	double curSongPos();
	double curSongLen();
	float curSongGainFactor();
	
	// returns the data read by the inStream.
	// if sampleNumOut==NULL, it will fill the requested samples with silence.
	// otherwise, it will say how much samples have been returned.
	// the outStream will call this. data read here is supposed to go without delay to the soundcard. it will update the timePos.
	// it is supposed to be fast. if no data is available, it will not wait for it but it will fill silence.
	// this returns the internal format, e.g. SINT16, outSamplerate and outNumChannels.
	// it might also issue the callbacks like song finished, or proceed to the next song - but it wont call them itself (for performance reasons).
	bool readOutStream(OUTSAMPLE_t* samples, size_t sampleNum, size_t* sampleNumOut);
	
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
	
	bool getNextSongLock;
	bool openPeekInStreamsLock;
	bool openStreamLock;
};

#endif

#endif
