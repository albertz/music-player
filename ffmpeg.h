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


#ifdef __cplusplus
struct PlayerObject;

extern "C" {
#endif

int initPlayerDecoder();
int initPlayerOutput();

extern PyTypeObject Player_Type;

PyObject* pyCreatePlayer(PyObject* self);
PyObject* pyGetSoundDevices(PyObject* self);
PyObject* pySetFfmpegLogLevel(PyObject* self, PyObject* args);
PyObject* pyEnableDebugLog(PyObject* self, PyObject* args);
PyObject* pyGetMetadata(PyObject* self, PyObject* args);
PyObject* pyCalcAcoustIdFingerprint(PyObject* self, PyObject* args);
PyObject* pyCalcBitmapThumbnail(PyObject* self, PyObject* args, PyObject* kws);
PyObject* pyCalcReplayGain(PyObject* self, PyObject* args, PyObject* kws);

#ifdef __cplusplus
}

#include "PyThreading.hpp"
#include "Buffer.hpp"
#include "SmoothClip.hpp"
#include "Fader.hpp"
#include "SampleType.hpp"
#include "LinkedList.hpp"
#include "PlayerInStream.hpp"

#include <boost/shared_ptr.hpp>
#include <boost/atomic.hpp>


// The player structure. Create by ffmpeg.createPlayer().
// This struct is initialized in player_init().
struct PlayerObject {
	PyObject_HEAD
	
	// public
	PyObject* queue;
	PyObject* peekQueue;
	PyObject* curSong;
	boost::atomic<bool> playing;
	bool soundcardOutputEnabled; // if enabled, uses PortAudio to play on soundcard. otherwise call readStreamOut manually
	std::string preferredSoundDevice;
	int setPlaying(bool playing);
	void resetPlaying();
	bool openOutStream();
	bool isOutStreamOpen();
	void closeOutStream(bool waitForPendingAudioBuffers);
	std::string getSoundDevice();
	float volume;
	SmoothClipCalc volumeSmoothClip; // see smoothClip()
	bool volumeAdjustEnabled;
	bool volumeAdjustNeeded(PlayerInStream* is = NULL) const;
	int outSamplerate;
	int outNumChannels;
	void setAudioTgt(int samplerate, int numchannels);
	double timeDelay(size_t sampleNum) { return double(sampleNum)/outSamplerate/outNumChannels; }
	Fader fader;
	boost::atomic<bool> outOfSync; // for readOutStream
	
	// private
	PyObject* dict;

	bool nextSongOnEof;
	bool skipPyExceptions; // for all callbacks, mainly song.readPacket
	
	int seekRel(double incr);
	int seekAbs(double pos);
	bool getNextSong(bool skipped);
	
	void workerProc(boost::atomic<bool>& stopSignal);
	PyThread workerThread;
	void startWorkerThread();
	
	typedef LinkedList<PlayerInStream> InStreams;
	InStreams inStreams;
	bool openInStream();
	bool tryOvertakePeekInStream();
	void openPeekInStreams();
	bool isInStreamOpened() const; // in case we hit EOF, it is still opened
	InStreams::ItemPtr getInStream() const; // old interface
	Buffer* inStreamBuffer();
	void resetBuffers();
	bool processInStream(); // returns true if there was no error
	PyObject* curSongMetadata() const;
	double curSongPos() const;
	double curSongLen() const;
	float curSongGainFactor() const;
	
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
	
	// Note: When enabling these, we expect to hold the player lock.
	// So while we hold the player lock, these can not be enabled from somewhere else.
	// These can be disabled though in unlocked scope.
	boost::atomic<bool> pyQueueLock; // This covers anything which would potentially modifiy `queue` or `peekQueue`.
	boost::atomic<bool> openStreamLock; // This covers the opening of a PlayerInStream. (Only because of FFmpeg issues. Maybe should be global. Should not be needed theoretically if FFmpeg would be safe.)
};

#endif

#endif
