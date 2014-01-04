#ifndef MP_PLAYERINSTREAM_HPP
#define MP_PLAYERINSTREAM_HPP

// INT64_MIN and co
#define __STDC_LIMIT_MACROS
#include <stdint.h>

extern "C" {
#include <libavformat/avformat.h>
#include <libswresample/swresample.h>
}

#include "SampleType.hpp"
#include "PyUtils.h"
#include "PyThreading.hpp"
#include "Buffer.hpp"
#include <boost/atomic.hpp>

struct PlayerObject;

struct AudioParams {
	int freq;
	int channels;
	int64_t channel_layout;
	enum AVSampleFormat fmt;
};

#define MAX_AUDIO_FRAME_SIZE 192000 // 1 second of 48khz 32bit audio

struct PlayerInStreamRawPOD {
	PlayerObject* player;
	PyObject* song;
	PyObject* metadata;
	double readerTimePos;
	double timeLen;
	float gainFactor;

	AVFormatContext* ctx;

	int audio_stream;
	double audio_clock;
	AVStream *audio_st;
	DECLARE_ALIGNED(OUTSAMPLEBITLEN,uint8_t,audio_buf2)[MAX_AUDIO_FRAME_SIZE * 4];
	uint8_t *audio_buf;
	AVPacket audio_pkt_temp;
	AVPacket audio_pkt;
	bool do_flush;
	struct AudioParams audio_tgt;
	struct AudioParams audio_src;
	struct SwrContext *swr_ctx;
	// 	int audio_write_buf_size;
	//    double audio_current_pts;
	//    double audio_current_pts_drift;
	AVFrame *frame;
};

struct PlayerInStream : PlayerInStreamRawPOD {
	// PlayerObject::lock must be unlocked before locking this!
	PyMutex lock;

	std::string debugName;
	Buffer outBuffer;
	bool readerHitEnd; // this will be set by audio_decode_frame()
	bool playerStartedPlaying; // this would be set by readOutStream()
	bool playerHitEnd; // this would be set by readOutStream()
	boost::atomic<double> playerTimePos;

	PlayerInStream() {
		mlock(this, sizeof(*this));
		memset(this, 0, sizeof(PlayerInStreamRawPOD));
		playerTimePos = 0;
		timeLen = -1;
		readerHitEnd = false;
		playerStartedPlaying = playerHitEnd = false;
	}
	~PlayerInStream();
	bool open(PlayerObject* player, PyObject* song);
	void resetBuffers();
	void seekToStart();
};


#endif // PLAYERINSTREAM_HPP
