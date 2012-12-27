// ffmpeg player decoding
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.


#include "ffmpeg.h"

#include <libavformat/avformat.h>
#include <libswresample/swresample.h>

#include <math.h>

#define AUDIO_BUFFER_SIZE	(2048 * 10)
#define PROCESS_SIZE		AUDIO_BUFFER_SIZE
#define BUFFER_FILL_SIZE	(48000 * 2 * 2 * 10) // 10secs for 48kHz,stereo - around 2MB

int initPlayerDecoder() {
	av_log_set_level(0);
	avcodec_register_all();
	av_register_all();
	return 0;
}

/*
 For values y < 0, mirror.
 For values y in [0,x1], this is just y (i.e. identity function).
 For values y >= x2, this is just 1 (i.e. constant 1 function).
 For y in [x1,x2], we use a cubic spline interpolation to just make it smooth.
 Use smoothClip_setX() to set the spline factors.
 */
double SmoothClipCalc::get(double y) {
	SmoothClipCalc* s = this;
	if(y < 0) return -get(-y);
	if(y <= s->x1) return y;
	if(y >= s->x2) return 1;
	y = s->a * y*y*y + s->b * y*y + s->c * y + s->d;
	if(y <= s->x1) return s->x1;
	if(y >= 1) return 1;
	return y;
}

void SmoothClipCalc::setX(float x1, float x2) {
	SmoothClipCalc* s = this;
	if(x1 < 0) x1 = 0;
	if(x1 > 1) x1 = 1;
	if(x2 < x1) x2 = x1;
	s->x1 = x1;
	s->x2 = x2;
	if(x1 == x2) {
		s->a = 0;
		s->b = 0;
		s->c = 1;
		s->d = 0;
		return;
	}
	s->a = ((x1 + x2 - 2.) / pow(x2 - x1, 3.));
	s->b = ((- (((x1 + x2 - 2.) * pow(x1, 2.)) / pow(x2 - x1, 3.)) - ((4. * x2 * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) + ((6. * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) - ((7. * pow(x2, 2.) * (x1 + x2 - 2.)) / pow(x2 - x1, 3.)) + ((6. * x2 * (x1 + x2 - 2.)) / pow(x2 - x1, 3.)) - 1.) / (4. * x2 - 4.));
	s->c = (1. / 2.) * ((((x1 + x2 - 2.) * pow(x1, 2.)) / pow(x2 - x1, 3.)) + ((4. * x2 * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) - ((6. * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) + ((pow(x2, 2.) * (x1 + x2 - 2.)) / pow(x2 - x1, 3.)) - ((6. * x2 * (x1 + x2 - 2.)) / pow(x2 - x1, 3.)) - ((4. * (- (((x1 + x2 - 2.) * pow(x1, 2.)) / pow(x2 - x1, 3.)) - ((4. * x2 * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) + ((6. * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) - ((7. * pow(x2, 2.) * (x1 + x2 - 2.)) / pow(x2 - x1, 3.)) + ((6. * x2 * (x1 + x2 - 2.)) / pow(x2 - x1, 3.)) - 1.)) / (4. * x2 - 4.)) + 1.);
	s->d = (1. / 4.) * ((((x1 + x2 - 2.) * pow(x1, 3.)) / pow(x2 - x1, 3.)) - ((4. * x2 * (x1 + x2 - 2.) * pow(x1, 2.)) / pow(x2 - x1, 3.)) - (((x1 + x2 - 2.) * pow(x1, 2.)) / pow(x2 - x1, 3.)) - ((pow(x2, 2.) * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) + ((2. * x2 * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) + ((6. * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) + x1 - ((pow(x2, 2.) * (x1 + x2 - 2.)) / pow(x2 - x1, 3.)) + ((6. * x2 * (x1 + x2 - 2.)) / pow(x2 - x1, 3.)) + ((4. * (- (((x1 + x2 - 2.) * pow(x1, 2.)) / pow(x2 - x1, 3.)) - ((4. * x2 * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) + ((6. * (x1 + x2 - 2.) * x1) / pow(x2 - x1, 3.)) - ((7. * pow(x2, 2.) * (x1 + x2 - 2.)) / pow(x2 - x1, 3.)) + ((6. * x2 * (x1 + x2 - 2.)) / pow(x2 - x1, 3.)) - 1.)) / (4. * x2 - 4.)) + 1.);
}

struct AudioParams {
	int freq;
	int channels;
	int64_t channel_layout;
	enum AVSampleFormat fmt;
};

struct InStreamRawPOD {
	PlayerObject* player;
	PyObject* song;
	PyObject* metadata;
	double timePos;
	double timeLen;
	float gainFactor;
	
	AVFormatContext* ctx;
	
	int audio_stream;
	double audio_clock;
	AVStream *audio_st;
	DECLARE_ALIGNED(16,uint8_t,audio_buf2)[AVCODEC_MAX_AUDIO_FRAME_SIZE * 4];
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

struct PlayerObject::InStream : InStreamRawPOD {
	Buffer outBuffer;
	bool readerHitEnd; // this will be set by audio_decode_frame()
	bool playerHitEnd; // this would be set by readOutStream()
	
	InStream() {
		memset(this, 0, sizeof(InStreamRawPOD));
		timeLen = -1;
		readerHitEnd = false;
		playerHitEnd = false;
	}
	~InStream();
	bool open(PlayerObject* player, PyObject* song);
	void resetBuffers();
};

static int player_read_packet(PlayerObject* player, uint8_t* buf, int buf_size) {
	// We assume that we have the PlayerObject lock at this point but not neccessarily the Python GIL.
	//printf("player_read_packet %i\n", buf_size);
	Py_ssize_t ret = -1;
	PyObject *readPacketFunc = NULL, *args = NULL, *retObj = NULL;
	
	PyGILState_STATE gstate;
	gstate = PyGILState_Ensure();
	if(player->curSong == NULL) goto final;
	
	readPacketFunc = PyObject_GetAttrString(player->curSong, "readPacket");
	if(readPacketFunc == NULL) goto final;
	
	args = PyTuple_New(1);
	PyTuple_SetItem(args, 0, PyInt_FromLong(buf_size));
	retObj = PyObject_CallObject(readPacketFunc, args);
	if(retObj == NULL) goto final;
	
	if(!PyString_Check(retObj)) {
		printf("song.readPacket didn't returned a string but a %s\n", retObj->ob_type->tp_name);
		goto final;
	}
	
	ret = PyString_Size(retObj);
	if(ret > buf_size) {
		printf("song.readPacket returned more than buf_size\n");
		ret = buf_size;
	}
	if(ret < 0) {
		ret = -1;
		goto final;
	}
	
	memcpy(buf, PyString_AsString(retObj), ret);
	
final:
	Py_XDECREF(retObj);
	Py_XDECREF(args);
	Py_XDECREF(readPacketFunc);
	
	if(player->skipPyExceptions && PyErr_Occurred())
		PyErr_Print();
	
	PyGILState_Release(gstate);
	return (int) ret;
}

static int64_t player_seek(PlayerObject* player, int64_t offset, int whence) {
	// We assume that we have the PlayerObject lock at this point but not neccessarily the Python GIL.
	//printf("player_seek %lli %i\n", offset, whence);
	int64_t ret = -1;
	PyGILState_STATE gstate;
	gstate = PyGILState_Ensure();
	PyObject *seekRawFunc = NULL, *args = NULL, *retObj = NULL;
	if(player->curSong == NULL) goto final;
	if(whence < 0 || whence > 2) goto final; // AVSEEK_SIZE and others not supported atm
	
	seekRawFunc = PyObject_GetAttrString(player->curSong, "seekRaw");
	if(seekRawFunc == NULL) goto final;
	
	args = PyTuple_New(2);
	if(args == NULL) goto final;
	PyTuple_SetItem(args, 0, PyLong_FromLongLong(offset));
	PyTuple_SetItem(args, 1, PyInt_FromLong(whence));
	retObj = PyObject_CallObject(seekRawFunc, args);
	if(retObj == NULL) goto final; // pass through any Python exception
	
	// NOTE: I don't really know what would be the best strategy in case of overflow...
	if(PyInt_Check(retObj))
		ret = (int) PyInt_AsLong(retObj);
	else if(PyLong_Check(retObj))
		ret = (int) PyLong_AsLong(retObj);
	else {
		printf("song.seekRaw didn't returned an int but a %s\n", retObj->ob_type->tp_name);
		goto final;
	}
	
final:
	Py_XDECREF(retObj);
	Py_XDECREF(args);
	Py_XDECREF(seekRawFunc);
	
	if(player->skipPyExceptions && PyErr_Occurred())
		PyErr_Print();
	
	PyGILState_Release(gstate);
	return ret;
}

static int _player_av_read_packet(void *opaque, uint8_t *buf, int buf_size) {
	return player_read_packet((PlayerObject*)opaque, buf, buf_size);
}

static int64_t _player_av_seek(void *opaque, int64_t offset, int whence) {
	return player_seek((PlayerObject*)opaque, offset, whence);
}

static
AVIOContext* initIoCtx(PlayerObject* player) {
	int buffer_size = 1024 * 4;
	unsigned char* buffer = (unsigned char*)av_malloc(buffer_size);
	
	AVIOContext* io = avio_alloc_context(
										 buffer,
										 buffer_size,
										 0, // writeflag
										 player, // opaque
										 _player_av_read_packet,
										 NULL, // write_packet
										 _player_av_seek
										 );
	
	return io;
}

static
AVFormatContext* initFormatCtx(PlayerObject* player) {
	AVFormatContext* fmt = avformat_alloc_context();
	if(!fmt) return NULL;
	
	fmt->pb = initIoCtx(player);
	if(!fmt->pb) {
		printf("initIoCtx failed\n");
	}
	
	fmt->flags |= AVFMT_FLAG_CUSTOM_IO;
	
	return fmt;
}


static void player_resetStreamPackets(PlayerObject::InStream* player) {
	av_free_packet(&player->audio_pkt);
	memset(&player->audio_pkt, 0, sizeof(player->audio_pkt));
	memset(&player->audio_pkt_temp, 0, sizeof(player->audio_pkt_temp));
}

void PlayerObject::InStream::resetBuffers() {
	this->do_flush = true;
	this->readerHitEnd = false;
	player_resetStreamPackets(this);
}

void PlayerObject::resetBuffers() {
	if(inStream.get())
		inStream->resetBuffers();
}

int PlayerObject::seekRel(double incr) {
	PlayerObject* pl = this;
	PlayerObject::InStream* player = pl->inStream.get();
	
	double pos = 0;
	/*
	 int seek_by_bytes = 0;
	if(seek_by_bytes) {
		if (player->audio_stream >= 0 && player->audio_pkt.pos >= 0) {
			pos = player->audio_pkt.pos;
		} else
			pos = avio_tell(player->ctx->pb);
		if (player->ctx->bit_rate)
			incr *= player->ctx->bit_rate / 8.0;
		else
			incr *= 180000.0;
		pos += incr;
	}
	else*/ {
		pos = player->timePos;
		pos += incr;
		player->timePos = pos;
		
		pos *= AV_TIME_BASE;
		incr *= AV_TIME_BASE;
	}
	
	int64_t seek_target = pos;
	int64_t seek_min    = incr > 0 ? seek_target - incr + 2: INT64_MIN;
	int64_t seek_max    = incr < 0 ? seek_target - incr - 2: INT64_MAX;
	int seek_flags = 0;
	//if(seek_by_bytes) seek_flags |= AVSEEK_FLAG_BYTE;
	
	pl->resetBuffers();
	
	return
	avformat_seek_file(
					   player->ctx, /*player->audio_stream*/ -1,
					   seek_min,
					   seek_target,
					   seek_max,
					   seek_flags
					   );
}

int PlayerObject::seekAbs(double pos) {
	PlayerObject* pl = this;
	PlayerObject::InStream* player = pl->inStream.get();
	int seek_by_bytes = 0;
	if(player->timeLen <= 0)
		seek_by_bytes = 1;
	
	player->timePos = pos;

	int seek_flags = 0;
	if(seek_by_bytes) seek_flags |= AVSEEK_FLAG_BYTE;
	
	if(seek_by_bytes) {
		if (player->ctx->bit_rate)
			pos *= player->ctx->bit_rate / 8.0;
		else
			pos *= 180000.0;
	}
	else {
		pos *= AV_TIME_BASE;
	}
	
	pl->resetBuffers();
	
	return
	avformat_seek_file(
					   player->ctx, /*player->audio_stream*/ -1,
					   INT64_MIN,
					   (int64_t) pos,
					   INT64_MAX,
					   seek_flags
					   );
}


/* open a given stream. Return 0 if OK */
// called by player_openInputStream()
static int stream_component_open(PlayerObject::InStream *is, AVFormatContext* ic, int stream_index)
{
	AVCodecContext *avctx;
	AVCodec *codec;
	//   AVDictionaryEntry *t = NULL;
	
	if (stream_index < 0 || stream_index >= ic->nb_streams)
		return -1;
	avctx = ic->streams[stream_index]->codec;
	
	codec = avcodec_find_decoder(avctx->codec_id);
	if (!codec) {
		printf("avcodec_find_decoder failed\n");
		return -1;
	}
	
	//avctx->workaround_bugs   = workaround_bugs;
	//avctx->lowres            = lowres;
	if(avctx->lowres > codec->max_lowres){
		av_log(avctx, AV_LOG_WARNING, "The maximum value for lowres supported by the decoder is %d\n",
			   codec->max_lowres);
		avctx->lowres= codec->max_lowres;
	}
	//avctx->idct_algo         = idct;
	//avctx->skip_frame        = skip_frame;
	//avctx->skip_idct         = skip_idct;
	//avctx->skip_loop_filter  = skip_loop_filter;
	//avctx->error_concealment = error_concealment;
	
	if(avctx->lowres) avctx->flags |= CODEC_FLAG_EMU_EDGE;
	//if (fast)   avctx->flags2 |= CODEC_FLAG2_FAST;
	if(codec->capabilities & CODEC_CAP_DR1)
		avctx->flags |= CODEC_FLAG_EMU_EDGE;
	
	if (avcodec_open2(avctx, codec, NULL /*opts*/) < 0) {
		printf("avcodec_open2 failed\n");
		return -1;
	}
	
	/* prepare audio output */
	//if (avctx->codec_type == AVMEDIA_TYPE_AUDIO) {
	//    is->audio_tgt = is->audio_src;
	//}
	
	ic->streams[stream_index]->discard = AVDISCARD_DEFAULT;
	switch (avctx->codec_type) {
		case AVMEDIA_TYPE_AUDIO:
			is->audio_stream = stream_index;
			is->audio_st = ic->streams[stream_index];
			
			/* init averaging filter */
			//is->audio_diff_avg_coef  = exp(log(0.01) / AUDIO_DIFF_AVG_NB);
			//is->audio_diff_avg_count = 0;
			/* since we do not have a precise anough audio fifo fullness,
			 we correct audio sync only if larger than this threshold */
			//is->audio_diff_threshold = 2.0 * is->audio_hw_buf_size / av_samples_get_buffer_size(NULL, is->audio_tgt.channels, is->audio_tgt.freq, is->audio_tgt.fmt, 1);
			
			player_resetStreamPackets(is);
			//packet_queue_start(&is->audioq);
			//SDL_PauseAudio(0);
			break;
		default:
			printf("stream_component_open: not an audio stream\n");
			return -1;
	}
	
	return 0;
}


static void player_setSongMetadata(PlayerObject::InStream* player) {
	Py_XDECREF(player->metadata);
	player->metadata = NULL;
	
	if(!player->ctx) return;
	if(!player->ctx->metadata) return;
	AVDictionary* m = player->ctx->metadata;
	
	player->metadata = PyDict_New();
	assert(player->metadata);
	
	AVDictionaryEntry *tag=NULL;
	while((tag=av_dict_get(m, "", tag, AV_DICT_IGNORE_SUFFIX))) {
		if(strcmp("language", tag->key) == 0)
			continue;
		
		PyDict_SetItemString_retain(player->metadata, tag->key, PyString_FromString(tag->value));
	}
	
	if(player->timeLen > 0) {
		PyDict_SetItemString_retain(player->metadata, "duration", PyFloat_FromDouble(player->timeLen));
	}
	else if(PyDict_GetItemString(player->metadata, "duration")) {
		// we have an earlier duration metadata which is a string now.
		// convert it to float.
		PyObject* floatObj = PyFloat_FromString(PyDict_GetItemString(player->metadata, "duration"), NULL);
		if(!floatObj) {
			PyErr_Clear();
			PyDict_DelItemString(player->metadata, "duration");
		}
		else {
			PyDict_SetItemString_retain(player->metadata, "duration", floatObj);
		}
	}
}

static void closeInputStream(AVFormatContext* formatCtx) {
	if(formatCtx->pb) {
		if(formatCtx->pb->buffer) {
			av_free(formatCtx->pb->buffer);
			formatCtx->pb->buffer = NULL;
		}
		// avformat_close_input freeing this indirectly? I got a crash here in avio_close
		//av_free(formatCtx->pb);
		//formatCtx->pb = NULL;
	}
	for(int i = 0; i < formatCtx->nb_streams; ++i) {
		avcodec_close(formatCtx->streams[i]->codec);
	}
	avformat_close_input(&formatCtx);
}

PlayerObject::InStream::~InStream() {
	PlayerObject::InStream* player = this;
	player_resetStreamPackets(player);
	if(player->ctx) {
		closeInputStream(player->ctx);
		player->ctx = NULL;
	}

	if(player->frame) {
		av_free(player->frame);
		player->frame = NULL;
	}
	
	if(player->swr_ctx) {
		swr_free(&player->swr_ctx);
		player->swr_ctx = NULL;
	}
	
	Py_XDECREF(song);
	song = NULL;
	
	Py_XDECREF(metadata);
	metadata = NULL;
}


bool PlayerObject::InStream::open(PlayerObject* pl, PyObject* song) {
	assert(song != NULL);
	
	if(this->player == NULL)
		this->player = pl;
	else {
		assert(this->player == pl);
	}
	
	Py_XDECREF(this->song); // if there is any old song
	Py_INCREF(song);
	this->song = song;
	
	InStream* player = this;
	int ret = 0;
	char* urlStr = NULL;
	
	AVFormatContext* formatCtx = initFormatCtx(pl);
	if(!formatCtx) {
		printf("initFormatCtx failed\n");
		goto final;
	}
	
	urlStr = objAttrStrDup(song, "url"); // the url is just for debugging, the song object provides its own IO
	ret = avformat_open_input(&formatCtx, urlStr, NULL, NULL);
	
	if(ret != 0) {
		printf("avformat_open_input failed\n");
		goto final;
	}
	
	ret = avformat_find_stream_info(formatCtx, NULL);
	if(ret < 0) {
		printf("avformat_find_stream_info failed\n");
		goto final;
	}
	
#ifdef DEBUG
	av_dump_format(formatCtx, 0, urlStr, 0);
#endif
	
	ret = av_find_best_stream(formatCtx, AVMEDIA_TYPE_AUDIO, -1, -1, 0, 0);
	if(ret < 0) {
		printf("no audio stream found in song\n");
		goto final;
	}
	player->audio_stream = ret;
	
	ret = stream_component_open(player, formatCtx, player->audio_stream);
	if(ret < 0) {
		printf("no audio stream found in song\n");
		goto final;
	}
	
	player->ctx = formatCtx;
	formatCtx = NULL;
	
	// Get the song len: There is formatCtx.duration in AV_TIME_BASE
	// and there is stream.duration in stream time base.
	assert(player->audio_st);
	this->timeLen = av_q2d(player->audio_st->time_base) * player->audio_st->duration;
	//if(player->timeLen < 0) { // happens in some cases, e.g. some flac files
	//	player->timeLen = av_q2d(AV_TIME_BASE_Q) * formatCtx->duration; // doesnt make it better though...
	//}
	if(this->timeLen < 0)
		this->timeLen = -1;
	
	player_setSongMetadata(this);
	
	this->gainFactor = 1;
	if(PyObject_HasAttrString(song, "gain")) {
		PyObject* gainObj = PyObject_GetAttrString(song, "gain");
		if(gainObj) {
			float gain = 0;
			if(!PyArg_Parse(gainObj, "f", &gain))
				printf("song.gain is not a float");
			else
				this->gainFactor = pow(10, gain / 20);
			Py_DECREF(gainObj);
		}
		else { // !gainObj
			// strange. reset any errors...
			if(PyErr_Occurred())
				PyErr_Print();
		}
	}
	// TODO: maybe alternatively try to read from metatags?
	
final:
	if(urlStr) free(urlStr);
	if(formatCtx) closeInputStream(formatCtx);
	if(this->ctx) return true;
	return false;
}

bool PlayerObject::openInStream() {	
	assert(this->curSong != NULL);
	
	this->inStream.reset(new PlayerObject::InStream());
	PlayerObject::InStream* player = this->inStream.get();
	
	if(!player->open(this, this->curSong)) {
		if(!this->nextSongOnEof) {
			// This means that the failure of opening is fatal because we wont skip to the next song.
			// This mode is also only used in the calc* specific functions.
			if(!PyErr_Occurred())
				PyErr_SetString(PyExc_RuntimeError, "failed to open file");
		}

		return false;
	}
	
	return true;
}



/* return the wanted number of samples to get better sync if sync_type is video
 * or external master clock */
static int synchronize_audio(PlayerObject::InStream *is, int nb_samples)
{
	int wanted_nb_samples = nb_samples;
	return wanted_nb_samples;
}

bool PlayerObject::volumeAdjustNeeded() const {
	if(this->volume != 1) return true;
	if(this->volumeSmoothClip.x1 != this->volumeSmoothClip.x2) return true;
	if(inStream.get() && inStream->gainFactor != 1) return true;
	return false;
}

static const enum AVSampleFormat outFormat = AV_SAMPLE_FMT_S16;

// called from player_fillOutStream
// decode one audio frame and returns its uncompressed size
// return <0 means that we must change some state for this function to work again. e.g. we could have EOF, the song is not correctly opened, the player is in stopped-state or so. an invalid frame will not cause this!
// note that even with <0, there might have been some data written to outBuffer.
// tries to return at least len bytes. but might return more. if something fails, also less.
static long audio_decode_frame(PlayerObject* player, PlayerObject::InStream *is, long len)
{
	// We assume that we have the PlayerObject lock at this point but not neccessarily the Python GIL.
	
	if(!player->playing) return -1;
	if(is->ctx == NULL) return -1;
	if(is->audio_st == NULL) return -1;
	if(is->readerHitEnd) return -1;
	
	AVPacket *pkt_temp = &is->audio_pkt_temp;
	AVPacket *pkt = &is->audio_pkt;
	AVCodecContext *dec = is->audio_st->codec;
	int len2, data_size, resampled_data_size;
	int64_t dec_channel_layout;
	int flush_complete = 0;
	int wanted_nb_samples;
	long count = 0;
	
	for (;;) {
		/* NOTE: the audio packet can contain several frames */
		while (pkt_temp->size > 0) {
			if (!is->frame) {
				if (!(is->frame = avcodec_alloc_frame()))
					return AVERROR(ENOMEM);
			} else
				avcodec_get_frame_defaults(is->frame);
						
			if (flush_complete)
				break;
			int got_frame = 0;
			int len1 = avcodec_decode_audio4(dec, is->frame, &got_frame, pkt_temp);
			if (len1 < 0) {
				/* if error, we skip the frame */
				pkt_temp->size = 0;
				break;
			}
			//printf("avcodec_decode_audio4: %i\n", len1);
			
			pkt_temp->data += len1;
			pkt_temp->size -= len1;
			
			if (!got_frame) {
				/* stop sending empty packets if the decoder is finished */
				if (!pkt_temp->data && dec->codec->capabilities & CODEC_CAP_DELAY)
					flush_complete = 1;
				continue;
			}
			data_size = av_samples_get_buffer_size(NULL, dec->channels,
												   is->frame->nb_samples,
												   dec->sample_fmt, 1);
			
			dec_channel_layout =
			(dec->channel_layout && dec->channels == av_get_channel_layout_nb_channels(dec->channel_layout)) ?
			dec->channel_layout : av_get_default_channel_layout(dec->channels);
			wanted_nb_samples = synchronize_audio(is, is->frame->nb_samples);
			
			if (dec->sample_fmt    != is->audio_src.fmt            ||
				dec_channel_layout != is->audio_src.channel_layout ||
				dec->sample_rate   != is->audio_src.freq           ||
				(wanted_nb_samples != is->frame->nb_samples && !is->swr_ctx) ||
				is->audio_tgt.freq != player->outSamplerate	||
				is->audio_tgt.channels != player->outNumChannels) {
				swr_free(&is->swr_ctx);
				
				is->audio_tgt.fmt = outFormat;
				is->audio_tgt.freq = player->outSamplerate;
				is->audio_tgt.channels = player->outNumChannels;
				is->audio_tgt.channel_layout = av_get_default_channel_layout(player->outNumChannels);
				
				is->swr_ctx = swr_alloc_set_opts
				(
					NULL,
					is->audio_tgt.channel_layout, outFormat, player->outSamplerate,
					 dec_channel_layout,           dec->sample_fmt,   dec->sample_rate,
					 0, NULL);
				if (!is->swr_ctx || swr_init(is->swr_ctx) < 0) {
					fprintf(stderr, "Cannot create sample rate converter for conversion of %d Hz %s %d channels to %d Hz %s %d channels!\n",
							dec->sample_rate,   av_get_sample_fmt_name(dec->sample_fmt),   dec->channels,
							player->outSamplerate, av_get_sample_fmt_name(outFormat), player->outNumChannels);
					break;
				}
				is->audio_src.channel_layout = dec_channel_layout;
				is->audio_src.channels = dec->channels;
				is->audio_src.freq = dec->sample_rate;
				is->audio_src.fmt = dec->sample_fmt;
				/*printf("conversion of %d Hz %s %d channels to %d Hz %s %d channels!\n",
				 dec->sample_rate,   av_get_sample_fmt_name(dec->sample_fmt),   dec->channels,
				 is->audio_tgt.freq, av_get_sample_fmt_name(is->audio_tgt.fmt), is->audio_tgt.channels);*/
			}
			
			if (is->swr_ctx) {
				const uint8_t **in = (const uint8_t **)is->frame->extended_data;
				uint8_t *out[] = {is->audio_buf2};
				int out_count = sizeof(is->audio_buf2) / player->outNumChannels / av_get_bytes_per_sample(outFormat);
				if (wanted_nb_samples != is->frame->nb_samples) {
					if (swr_set_compensation(is->swr_ctx, (wanted_nb_samples - is->frame->nb_samples) * player->outSamplerate / dec->sample_rate,
											 wanted_nb_samples * player->outSamplerate / dec->sample_rate) < 0) {
						fprintf(stderr, "swr_set_compensation() failed\n");
						break;
					}
				}
				len2 = swr_convert(is->swr_ctx, out, out_count, in, is->frame->nb_samples);
				if (len2 < 0) {
					fprintf(stderr, "swr_convert() failed\n");
					break;
				}
				if (len2 == out_count) {
					fprintf(stderr, "warning: audio buffer is probably too small\n");
					swr_init(is->swr_ctx);
				}
				is->audio_buf = is->audio_buf2;
				resampled_data_size = len2 * player->outNumChannels * av_get_bytes_per_sample(outFormat);
			} else {
				is->audio_buf = is->frame->data[0];
				resampled_data_size = data_size;
			}
			
			if(player->volumeAdjustNeeded()) {
				for(size_t i = 0; i < resampled_data_size / 2; ++i) {
					int16_t* sampleAddr = (int16_t*) is->audio_buf + i;
					int32_t sample = *sampleAddr; // TODO: endian swap?
					double sampleFloat = sample / ((double) 0x8000);
					
					sampleFloat *= player->volume;
					sampleFloat *= is->gainFactor;
					
					sampleFloat = player->volumeSmoothClip.get(sampleFloat);
					if(sampleFloat < -1) sampleFloat = -1;
					if(sampleFloat > 1) sampleFloat = 1;
					
					sample = sampleFloat * (double) 0x8000;
					if(sample < -0x8000) sample = -0x8000;
					if(sample > 0x7fff) sample = 0x7fff;
					*sampleAddr = (int16_t) sample; // TODO: endian swap?
				}
			}
			
			is->outBuffer.push(is->audio_buf, resampled_data_size);
			
			/* if no pts, then compute it */
			/*player->curSongPos += (double)data_size /
			(dec->channels * dec->sample_rate * av_get_bytes_per_sample(dec->sample_fmt));*/
			/*{
			 static double last_clock;
			 printf("audio: delay=%0.3f clock=%0.3f pts=%0.3f\n",
			 is->audio_clock - last_clock,
			 is->audio_clock, pts);
			 last_clock = is->audio_clock;
			 }*/
			count += resampled_data_size;
			if(count >= len)
				return count;
		}
		
		/* free the current packet */
		av_free_packet(pkt);
		memset(pkt_temp, 0, sizeof(*pkt_temp));
						
		if(is->do_flush) {
			avcodec_flush_buffers(dec);
			flush_complete = 0;
			is->do_flush = false;
		}
		
		while(1) {
			int ret = av_read_frame(is->ctx, pkt);
			if (ret < 0) {
				//if (ic->pb && ic->pb->error)
				//	printf("av_read_frame error\n");
				//if (ret == AVERROR_EOF || url_feof(is->ctx->pb))
				// no matter what, set hitEnd because we want to proceed with the next song and don't know what to do here otherwise.
				is->readerHitEnd = true;
				return count;
			}
			
			if(pkt->stream_index == is->audio_stream)
				break;
			
			av_free_packet(pkt);
		}
		
		*pkt_temp = *pkt;
		
		/* if update the audio clock with the pts */
		if (pkt->pts != AV_NOPTS_VALUE) {
			if(is->outBuffer.empty())
				is->timePos = av_q2d(is->audio_st->time_base)*pkt->pts;
		}
	}
}

bool PlayerObject::buffersFullEnough() const {
	PlayerObject::InStream* is = this->inStream.get();
	if(!is) return true;
	if(is->playerHitEnd) return true;
	size_t c = 0;
	for(auto& it : is->outBuffer.chunks) {
		c += it.size();
		if(c >= BUFFER_FILL_SIZE) return true;
	}
	return false;
}

bool PlayerObject::processInStream() {
	PlayerObject::InStream* is = this->inStream.get();
	if(!is) return false;
	if(audio_decode_frame(this, is, PROCESS_SIZE) < 0)
		return false;
	return true;
}

bool PlayerObject::isInStreamOpened() const {
	if(inStream.get() == NULL) return false;
	if(inStream->ctx == NULL) return false;
	return true;
}

Buffer* PlayerObject::inStreamBuffer() {
	if(inStream.get()) return &inStream->outBuffer;
	return NULL;
}

static void loopFrame(PlayerObject* player) {
	// We must not hold the PyGIL here!
	
	{
		PyScopedLock lock(player->lock);
		
		if(!player->isInStreamOpened() && player->nextSongOnEof) {
			PyGILState_STATE gstate;
			gstate = PyGILState_Ensure();
			
			if(!player->getNextSong(false)) {
				fprintf(stderr, "cannot get next song\n");
				if(PyErr_Occurred())
					PyErr_Print();
			}
			
			PyGILState_Release(gstate);
		}
	}
	
	{
		PyScopedLock lock(player->lock);
		if(!player->buffersFullEnough())
			player->processInStream();
	}
	
	{
		PyScopedLock lock(player->lock);

		PlayerObject::InStream* is = player->inStream.get();
		if(is && is->playerHitEnd && player->nextSongOnEof) {
			PyGILState_STATE gstate;
			gstate = PyGILState_Ensure();
			
			if(player->dict) {
				Py_INCREF(player->dict);
				PyObject* onSongFinished = PyDict_GetItemString(player->dict, "onSongFinished");
				if(onSongFinished && onSongFinished != Py_None) {
					Py_INCREF(onSongFinished);
					
					PyObject* kwargs = PyDict_New();
					assert(kwargs);
					if(player->curSong)
						PyDict_SetItemString(kwargs, "song", player->curSong);
					
					PyObject* retObj = PyEval_CallObjectWithKeywords(onSongFinished, NULL, kwargs);
					Py_XDECREF(retObj);
					
					// errors are not fatal from the callback, so handle it now and go on
					if(PyErr_Occurred())
						PyErr_Print();
					
					Py_DECREF(kwargs);
					Py_DECREF(onSongFinished);
				}
				Py_DECREF(player->dict);
			}
			
			// switch to next song
			player->getNextSong(false);
			if(PyErr_Occurred())
				PyErr_Print();
			
			PyGILState_Release(gstate);			
		}
	}
}

bool PlayerObject::readOutStream(int16_t* samples, size_t sampleNum) {
	// We must not hold the PyGIL here!
	PyScopedLock lock(this->lock);

	PlayerObject::InStream* is = this->inStream.get();
	if(is) {
		size_t byteCount = is->outBuffer.pop((uint8_t*)samples, sampleNum*2);
		samples += byteCount / 2;
		sampleNum -= byteCount / 2;
		is->timePos += timeDelay(byteCount / 2);
	}

	if(sampleNum > 0) {
		// silence
		memset((uint8_t*)samples, 0, sampleNum*2);
		
		if(is && is->readerHitEnd)
			is->playerHitEnd = true;
	}

	// TODO: later, just proceed with peekInStream. gapless playback
	
	return sampleNum == 0;
}

PyObject *
pySetFfmpegLogLevel(PyObject* self, PyObject* args) {
	int level = 0;
	if(!PyArg_ParseTuple(args, "i:setFfmpegLogLevel", &level))
		return NULL;
	
	av_log_set_level(level);
	
	Py_INCREF(Py_None);
	return Py_None;
}


