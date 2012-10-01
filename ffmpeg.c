// Python module for playing audio

// compile:
// gcc -c ffmpeg.o -I /System/Library/Frameworks/Python.framework/Headers/
// libtool -dynamic -o ffmpeg.so ffmpeg.o -framework Python -lavformat -lavutil -lavcodec -lswresample -lportaudio -lc

// loosely based on ffplay.c
// https://github.com/FFmpeg/ffmpeg/blob/master/ffplay.c

// Similar to PyFFmpeg. http://code.google.com/p/pyffmpeg/
// This module is intended to be much simpler/high-level, though.

// Pyton interface:
//	createPlayer() -> player object with:
//		queue: song generator
//		playing: True or False, initially False
//		curSong: current song (read only)
//		curSongPos: current song pos (read only)
//		curSongLen: current song len (read only)
//		seekAbs(t) / seekRel(t): seeking functions (t in seconds, accepts float)
//		nextSong(): skip to next song function
//	song object expected interface:
//		url: some url, can be anything
//		readPacket(bufSize): should return some string
//		seekRaw(offset, whence): should seek and return the current pos

#include <libavformat/avformat.h>
#include <libswresample/swresample.h>
#include <libavcodec/avfft.h>
#include <portaudio.h>
#include <Python.h>
#include <pythread.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <chromaprint.h>

//#define DEBUG 1

#define SAMPLERATE 44100
#define NUMCHANNELS 2
#define AUDIO_BUFFER_SIZE 2048

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

typedef struct AudioParams {
    int freq;
    int channels;
    int64_t channel_layout;
    enum AVSampleFormat fmt;
} AudioParams;

// see smoothClip()
typedef struct SmoothClipCalc {
	float x1, x2;
	double a,b,c,d;
} SmoothClipCalc;

// The player structure. Create by ffmpeg.createPlayer().
// This struct is initialized in player_init().
typedef struct {
    PyObject_HEAD
	
	// public
	PyObject* queue;
    int playing;
	PyObject* curSong;
	double curSongLen;
	PyObject* curSongMetadata;
	
	// private
	AVFormatContext* inStream;
	PaStream* outStream;
	PyObject* dict;
	int nextSongOnEof;
	float volume;
	SmoothClipCalc volumeSmoothClip; // see smoothClip()
	
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
	PyThread_type_lock lock;
	
	// audio_decode
    int audio_stream;
    double audio_clock;
    AVStream *audio_st;
    DECLARE_ALIGNED(16,uint8_t,audio_buf2)[AVCODEC_MAX_AUDIO_FRAME_SIZE * 4];
    uint8_t silence_buf[AUDIO_BUFFER_SIZE];
    uint8_t *audio_buf;
    uint8_t *audio_buf1;
    unsigned int audio_buf_size; /* in bytes */
    int audio_buf_index; /* in bytes */
    int audio_write_buf_size;
    AVPacket audio_pkt_temp;
    AVPacket audio_pkt;
	int do_flush;
    struct AudioParams audio_src;
    struct AudioParams audio_tgt;
    struct SwrContext *swr_ctx;
//    double audio_current_pts;
//    double audio_current_pts_drift;
	AVFrame *frame;

} PlayerObject;

/*
For values y < 0, mirror.
For values y in [0,x1], this is just y (i.e. identity function).
For values y >= x2, this is just 1 (i.e. constant 1 function).
For y in [x1,x2], we use a cubic spline interpolation to just make it smooth.
Use smoothClip_setX() to set the spline factors.
*/
static double smoothClip(SmoothClipCalc* s, double y) {
	if(y < 0) return -smoothClip(s, -y);
	if(y <= s->x1) return y;
	if(y >= s->x2) return 1;
	y = s->a * y*y*y + s->b * y*y + s->c * y + s->d;
	if(y <= s->x1) return s->x1;
	if(y >= 1) return 1;
	return y;
}

static void smoothClip_setX(SmoothClipCalc* s, float x1, float x2) {
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
	s->a = ((x1 + x2 - 2) / pow(x2 - x1, 3));
	s->b = ((- (((x1 + x2 - 2) * pow(x1, 2)) / pow(x2 - x1, 3)) - ((4 * x2 * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) + ((6 * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) - ((7 * pow(x2, 2) * (x1 + x2 - 2)) / pow(x2 - x1, 3)) + ((6 * x2 * (x1 + x2 - 2)) / pow(x2 - x1, 3)) - 1) / (4 * x2 - 4));
	s->c = (1 / 2) * ((((x1 + x2 - 2) * pow(x1, 2)) / pow(x2 - x1, 3)) + ((4 * x2 * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) - ((6 * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) + ((pow(x2, 2) * (x1 + x2 - 2)) / pow(x2 - x1, 3)) - ((6 * x2 * (x1 + x2 - 2)) / pow(x2 - x1, 3)) - ((4 * (- (((x1 + x2 - 2) * pow(x1, 2)) / pow(x2 - x1, 3)) - ((4 * x2 * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) + ((6 * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) - ((7 * pow(x2, 2) * (x1 + x2 - 2)) / pow(x2 - x1, 3)) + ((6 * x2 * (x1 + x2 - 2)) / pow(x2 - x1, 3)) - 1)) / (4 * x2 - 4)) + 1);
	s->d = (1 / 4) * ((((x1 + x2 - 2) * pow(x1, 3)) / pow(x2 - x1, 3)) - ((4 * x2 * (x1 + x2 - 2) * pow(x1, 2)) / pow(x2 - x1, 3)) - (((x1 + x2 - 2) * pow(x1, 2)) / pow(x2 - x1, 3)) - ((pow(x2, 2) * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) + ((2 * x2 * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) + ((6 * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) + x1 - ((pow(x2, 2) * (x1 + x2 - 2)) / pow(x2 - x1, 3)) + ((6 * x2 * (x1 + x2 - 2)) / pow(x2 - x1, 3)) + ((4 * (- (((x1 + x2 - 2) * pow(x1, 2)) / pow(x2 - x1, 3)) - ((4 * x2 * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) + ((6 * (x1 + x2 - 2) * x1) / pow(x2 - x1, 3)) - ((7 * pow(x2, 2) * (x1 + x2 - 2)) / pow(x2 - x1, 3)) + ((6 * x2 * (x1 + x2 - 2)) / pow(x2 - x1, 3)) - 1)) / (4 * x2 - 4)) + 1);
}

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
	
	if(PyErr_Occurred())
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
	
	if(PyErr_Occurred())
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
	unsigned char* buffer = av_malloc(buffer_size);
	
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

static int stream_seekRel(PlayerObject* player, double incr) {
	int seek_by_bytes = 0;
	
	double pos = 0;
	if(seek_by_bytes) {
		if (player->audio_stream >= 0 && player->audio_pkt.pos >= 0) {
			pos = player->audio_pkt.pos;
		} else
			pos = avio_tell(player->inStream->pb);
		if (player->inStream->bit_rate)
			incr *= player->inStream->bit_rate / 8.0;
		else
			incr *= 180000.0;
		pos += incr;
	}
	else {
		pos = player->audio_clock;
		pos += incr;
		
		pos *= AV_TIME_BASE;
		incr *= AV_TIME_BASE;
	}
	
	int64_t seek_target = pos;
	int64_t seek_min    = incr > 0 ? seek_target - incr + 2: INT64_MIN;
	int64_t seek_max    = incr < 0 ? seek_target - incr - 2: INT64_MAX;
	int seek_flags = 0;
	if(seek_by_bytes) seek_flags |= AVSEEK_FLAG_BYTE;
	
	player->do_flush = 1;
	
	return
	avformat_seek_file(
		player->inStream, /*player->audio_stream*/ -1,
		seek_min,
		seek_target,
		seek_max,
		seek_flags
		);
}

static int stream_seekAbs(PlayerObject* player, double pos) {
	int seek_by_bytes = 0;
	if(player->curSongLen <= 0)
		seek_by_bytes = 1;
		
	int seek_flags = 0;
	if(seek_by_bytes) seek_flags |= AVSEEK_FLAG_BYTE;

	if(seek_by_bytes) {
		if (player->inStream->bit_rate)
			pos *= player->inStream->bit_rate / 8.0;
		else
			pos *= 180000.0;
	}
	else {
		pos *= AV_TIME_BASE;
	}
	
	player->do_flush = 1;

	return
	avformat_seek_file(
		player->inStream, /*player->audio_stream*/ -1,
		INT64_MIN,
		(int64_t) pos,
		INT64_MAX,
		seek_flags
		);
}

static void player_resetStreamPackets(PlayerObject* player) {
	av_free_packet(&player->audio_pkt);
	memset(&player->audio_pkt, 0, sizeof(player->audio_pkt));
	memset(&player->audio_pkt_temp, 0, sizeof(player->audio_pkt_temp));
}

/* open a given stream. Return 0 if OK */
// called by player_openInputStream()
static int stream_component_open(PlayerObject *is, AVFormatContext* ic, int stream_index)
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
			is->audio_buf_size  = 0;
			is->audio_buf_index = 0;
			
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

static char* objStrDup(PyObject* obj) {
	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject* strObj = obj ? PyObject_Str(obj) : NULL;
	char* str = strObj ? PyString_AsString(strObj) : "<None>";
	str = strdup(str);
	Py_XDECREF(strObj);
	PyGILState_Release(gstate);
	return str;
}

static char* objAttrStrDup(PyObject* obj, const char* attrStr) {
	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject* attrObj = PyObject_GetAttrString(obj, attrStr);
	char* str = objStrDup(attrObj);
	Py_XDECREF(attrObj);
	PyGILState_Release(gstate);
	return str;
}

static void player_setSongMetadata(PlayerObject* player) {
	Py_XDECREF(player->curSongMetadata);
	player->curSongMetadata = NULL;
	
	if(!player->inStream) return;
	if(!player->inStream->metadata) return;
	AVDictionary* m = player->inStream->metadata;
	
	player->curSongMetadata = PyDict_New();
	assert(player->curSongMetadata);
	
	AVDictionaryEntry *tag=NULL;
	while((tag=av_dict_get(m, "", tag, AV_DICT_IGNORE_SUFFIX))) {
		if(strcmp("language", tag->key) == 0)
			continue;
		
		PyObject* value = PyString_FromString(tag->value);
		PyDict_SetItemString(player->curSongMetadata, tag->key, value);
		Py_DECREF(value);
	}
	
	if(player->curSongLen > 0) {
		PyObject* value = PyFloat_FromDouble(player->curSongLen);
		PyDict_SetItemString(player->curSongMetadata, "duration", value);
		Py_DECREF(value);
	}
	else if(PyDict_GetItemString(player->curSongMetadata, "duration")) {
		// we have an earlier duration metadata which is a string now.
		// convert it to float.
		PyObject* floatObj = PyFloat_FromString(PyDict_GetItemString(player->curSongMetadata, "duration"), NULL);
		if(!floatObj) {
			PyErr_Clear();
			PyDict_DelItemString(player->curSongMetadata, "duration");
		}
		else {
			PyDict_SetItemString(player->curSongMetadata, "duration", floatObj);
			Py_DECREF(floatObj);
		}
	}
}

static void closeInputStream(AVFormatContext* formatCtx) {
	if(formatCtx->pb) {
		if(formatCtx->pb->buffer) {
			av_free(formatCtx->pb->buffer);
			formatCtx->pb->buffer = NULL;
		}
		av_free(formatCtx->pb);
		formatCtx->pb = NULL;
	}
	for(int i = 0; i < formatCtx->nb_streams; ++i) {
		avcodec_close(formatCtx->streams[i]->codec);
	}
	avformat_close_input(&formatCtx);
}

static void player_closeInputStream(PlayerObject* player) {
	player_resetStreamPackets(player);
	if(player->inStream) {
		closeInputStream(player->inStream);
		player->inStream = NULL;
	}
}

static
int player_openInputStream(PlayerObject* player) {
	char* urlStr = NULL;

	assert(player->curSong != NULL);
	PyObject* curSong = player->curSong;
	
	player_closeInputStream(player);
	
	AVFormatContext* formatCtx = initFormatCtx(player);
	if(!formatCtx) {
		printf("initFormatCtx failed\n");
		goto final;
	}
	
	urlStr = objAttrStrDup(curSong, "url"); // the url is just for debugging, the song object provides its own IO
	int ret = avformat_open_input(&formatCtx, urlStr, NULL, NULL);

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
		
	player->inStream = formatCtx;
	formatCtx = NULL;
	
	// Get the song len: There is formatCtx.duration in AV_TIME_BASE
	// and there is stream.duration in stream time base.
	assert(player->audio_st);
	player->curSongLen = av_q2d(player->audio_st->time_base) * player->audio_st->duration;
	//if(player->curSongLen < 0) { // happens in some cases, e.g. some flac files
	//	player->curSongLen = av_q2d(AV_TIME_BASE_Q) * formatCtx->duration; // doesnt make it better though...
	//}
	if(player->curSongLen < 0)
		player->curSongLen = -1;
	
	player_setSongMetadata(player);

final:
	if(urlStr) free(urlStr);
	if(formatCtx) closeInputStream(formatCtx);
	if(player->inStream) return 0;
	return -1;
}

static int player_getNextSong(PlayerObject* player, int skipped) {
	// We must hold the player lock here.
	int ret = -1;
	PyGILState_STATE gstate;
	gstate = PyGILState_Ensure();
	
	PyObject* oldSong = player->curSong;
	player->curSong = NULL;
	
	if(player->queue == NULL) {
		PyErr_SetString(PyExc_RuntimeError, "player queue is not set");
		goto final;
	}
	
	if(!PyIter_Check(player->queue)) {
		PyErr_SetString(PyExc_RuntimeError, "player queue is not an iterator");
		goto final;
	}
	
	player->curSong = PyIter_Next(player->queue);
	
	// pass through any Python errors
	if(!player->curSong || PyErr_Occurred())
		goto final;
	
	if(player->curSong && player_openInputStream(player) != 0) {
		// This is not fatal, so don't make a Python exception.
		// When we are in playing state, we will just skip to the next song.
		// This can happen if we don't support the format or whatever.
		printf("cannot open input stream\n");
	}
		
	if(player->curSong) {
		if(player->dict) {
			Py_INCREF(player->dict);
			PyObject* onSongChange = PyDict_GetItemString(player->dict, "onSongChange");
			if(onSongChange && onSongChange != Py_None) {
				Py_INCREF(onSongChange);
				
				PyObject* kwargs = PyDict_New();
				assert(kwargs);
				if(oldSong)
					PyDict_SetItemString(kwargs, "oldSong", oldSong);
				else
					PyDict_SetItemString(kwargs, "oldSong", Py_None);
				PyDict_SetItemString(kwargs, "newSong", player->curSong);
				PyObject* skippedObj = PyBool_FromLong(skipped);
				PyDict_SetItemString(kwargs, "skipped", PyBool_FromLong(skipped));
				Py_DECREF(skippedObj);
				
				PyObject* retObj = PyEval_CallObjectWithKeywords(onSongChange, NULL, kwargs);
				Py_XDECREF(retObj);
				
				// errors are not fatal from the callback, so handle it now and go on
				if(PyErr_Occurred()) {
					PyErr_Print(); // prints traceback to stderr, resets error indicator. also handles sys.excepthook if it is set (see pythonrun.c, it's not said explicitely in the docs)
				}
				
				Py_DECREF(kwargs);
				Py_DECREF(onSongChange);
			}
			Py_DECREF(player->dict);
		}
	}

	if(player->curSong && player->inStream)
		ret = 0;
	
final:
	Py_XDECREF(oldSong);
	PyGILState_Release(gstate);
	return ret;
}

/* return the wanted number of samples to get better sync if sync_type is video
 * or external master clock */
static int synchronize_audio(PlayerObject *is, int nb_samples)
{
    int wanted_nb_samples = nb_samples;
	return wanted_nb_samples;	
}

static int volumeAdjustNeeded(PlayerObject* p) {
	if(p->volume != 1) return 1;
	if(p->volumeSmoothClip.x1 != p->volumeSmoothClip.x2) return 1;
	return 0;
}

// called from player_fillOutStream
/* decode one audio frame and returns its uncompressed size */
static int audio_decode_frame(PlayerObject *is, double *pts_ptr)
{
	// We assume that we have the PlayerObject lock at this point but not neccessarily the Python GIL.

	if(is->inStream == NULL) return -1;
	if(is->audio_st == NULL) return -1;
	
    AVPacket *pkt_temp = &is->audio_pkt_temp;
    AVPacket *pkt = &is->audio_pkt;
    AVCodecContext *dec = is->audio_st->codec;
    int len1, len2, data_size, resampled_data_size;
    int64_t dec_channel_layout;
    int got_frame;
    double pts;
    int new_packet = 0;
    int flush_complete = 0;
    int wanted_nb_samples;
	
    for (;;) {
        /* NOTE: the audio packet can contain several frames */
        while (pkt_temp->size > 0 || (!pkt_temp->data && new_packet)) {
            if (!is->frame) {
                if (!(is->frame = avcodec_alloc_frame()))
                    return AVERROR(ENOMEM);
            } else
                avcodec_get_frame_defaults(is->frame);
			
            if (!is->playing)
                return -1;
			
            if (flush_complete)
                break;
            new_packet = 0;
            len1 = avcodec_decode_audio4(dec, is->frame, &got_frame, pkt_temp);
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
                (wanted_nb_samples != is->frame->nb_samples && !is->swr_ctx)) {
                swr_free(&is->swr_ctx);
                is->swr_ctx = swr_alloc_set_opts(NULL,
                                                 is->audio_tgt.channel_layout, is->audio_tgt.fmt, is->audio_tgt.freq,
                                                 dec_channel_layout,           dec->sample_fmt,   dec->sample_rate,
                                                 0, NULL);
                if (!is->swr_ctx || swr_init(is->swr_ctx) < 0) {
                    fprintf(stderr, "Cannot create sample rate converter for conversion of %d Hz %s %d channels to %d Hz %s %d channels!\n",
							dec->sample_rate,   av_get_sample_fmt_name(dec->sample_fmt),   dec->channels,
							is->audio_tgt.freq, av_get_sample_fmt_name(is->audio_tgt.fmt), is->audio_tgt.channels);
                    break;
                }
                is->audio_src.channel_layout = dec_channel_layout;
                is->audio_src.channels = dec->channels;
                is->audio_src.freq = dec->sample_rate;
                is->audio_src.fmt = dec->sample_fmt;
            }
			
            if (is->swr_ctx) {
                const uint8_t **in = (const uint8_t **)is->frame->extended_data;
                uint8_t *out[] = {is->audio_buf2};
                int out_count = sizeof(is->audio_buf2) / is->audio_tgt.channels / av_get_bytes_per_sample(is->audio_tgt.fmt);
                if (wanted_nb_samples != is->frame->nb_samples) {
                    if (swr_set_compensation(is->swr_ctx, (wanted_nb_samples - is->frame->nb_samples) * is->audio_tgt.freq / dec->sample_rate,
											 wanted_nb_samples * is->audio_tgt.freq / dec->sample_rate) < 0) {
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
                resampled_data_size = len2 * is->audio_tgt.channels * av_get_bytes_per_sample(is->audio_tgt.fmt);
            } else {
                is->audio_buf = is->frame->data[0];
                resampled_data_size = data_size;
            }
			
			if(volumeAdjustNeeded(is)) {
				for(size_t i = 0; i < resampled_data_size / 2; ++i) {
					int16_t* sampleAddr = (int16_t*) is->audio_buf + i;
					int16_t sample = *sampleAddr; // TODO: endian swap?
					float sampleFloat = sample / ((float) 0x8000);
					
					sampleFloat *= is->volume;
					sampleFloat = smoothClip(&is->volumeSmoothClip, sampleFloat);
					if(sampleFloat < -1) sampleFloat = -1;
					if(sampleFloat > 1) sampleFloat = 1;
					
					sample = sampleFloat * (float) 0x8000;
					if(sample < -0x8000) sample = -0x8000;
					if(sample > 0x7fff) sample = 0x7fff;
					*sampleAddr = sample; // TODO: endian swap?
				}
			}
			
            /* if no pts, then compute it */
            pts = is->audio_clock;
            *pts_ptr = pts;
            is->audio_clock += (double)data_size /
			(dec->channels * dec->sample_rate * av_get_bytes_per_sample(dec->sample_fmt));
            /*{
                static double last_clock;
                printf("audio: delay=%0.3f clock=%0.3f pts=%0.3f\n",
                       is->audio_clock - last_clock,
                       is->audio_clock, pts);
                last_clock = is->audio_clock;
            }*/
            return resampled_data_size;
        }
		
        /* free the current packet */
		av_free_packet(pkt);
		memset(pkt_temp, 0, sizeof(*pkt_temp));
		
        if (!is->playing /* || is->audioq.abort_request */) {
            return -1;
        }
		
        /* read next packet */
        /*if ((new_packet = packet_queue_get(&is->audioq, pkt, 1)) < 0)
            return -1;
		
        if (pkt->data == flush_pkt.data) {
            avcodec_flush_buffers(dec);
            flush_complete = 0;
        }
		*/
		
		if(is->do_flush) {
			avcodec_flush_buffers(dec);
			flush_complete = 0;
			is->do_flush = 0;
		}
		
		while(1) {
			int ret = av_read_frame(is->inStream, pkt);
			if (ret < 0) {
				//if (ic->pb && ic->pb->error)
				//	printf("av_read_frame error\n");
				int eof = 0;
				if (ret == AVERROR_EOF || url_feof(is->inStream->pb))
					eof = 1;
				if(eof && is->nextSongOnEof) {
					PyGILState_STATE gstate;
					gstate = PyGILState_Ensure();

					PlayerObject* player = is;
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
					player_getNextSong(is, 0);
					if(PyErr_Occurred())
						PyErr_Print();
						
					PyGILState_Release(gstate);
				}
				return -1;
			}
			
			if(pkt->stream_index == is->audio_stream)
				break;

			av_free_packet(pkt);
		}
		
        *pkt_temp = *pkt;
		
        /* if update the audio clock with the pts */
        if (pkt->pts != AV_NOPTS_VALUE) {
            is->audio_clock = av_q2d(is->audio_st->time_base)*pkt->pts;
        }
    }
}

// called from paStreamCallback
static
int player_fillOutStream(PlayerObject* player, uint8_t* stream, unsigned long len) {
	// We must not hold the PyGIL here!
	PyThread_acquire_lock(player->lock, WAIT_LOCK);

	if(player->inStream == NULL && player->nextSongOnEof) {
		PyGILState_STATE gstate;
		gstate = PyGILState_Ensure();

		if(player_getNextSong(player, 0) != 0) {
			fprintf(stderr, "cannot get next song\n");
			if(PyErr_Occurred())
				PyErr_Print();
		}
		
		PyGILState_Release(gstate);
	}
	
	PlayerObject* is = player;
	int audio_size;
    unsigned long len1;
    int bytes_per_sec;
    int frame_size = av_samples_get_buffer_size(NULL, is->audio_tgt.channels, 1, is->audio_tgt.fmt, 1);
    double pts;
	
   // audio_callback_time = av_gettime();
	
	//printf("player_fillOutStream %i %i %i\n", len, is->audio_buf_index, is->audio_buf_size);
    while (len > 0) {
        if (is->audio_buf_index >= is->audio_buf_size) {
			audio_size = audio_decode_frame(is, &pts);
			if (audio_size < 0) {
                /* if error, just output silence */
				is->audio_buf      = is->silence_buf;
				is->audio_buf_size = sizeof(is->silence_buf) / frame_size * frame_size;
			} else {
				is->audio_buf_size = audio_size;
			}
			is->audio_buf_index = 0;
        }
        len1 = is->audio_buf_size - is->audio_buf_index;
        if (len1 > len)
            len1 = len;
        memcpy(stream, (uint8_t *)is->audio_buf + is->audio_buf_index, len1);
        len -= len1;
        stream += len1;
        is->audio_buf_index += len1;
    }
    bytes_per_sec = is->audio_tgt.freq * is->audio_tgt.channels * av_get_bytes_per_sample(is->audio_tgt.fmt);
    is->audio_write_buf_size = is->audio_buf_size - is->audio_buf_index;
    /* Let's assume the audio driver that is used by SDL has two periods. */
  //  is->audio_current_pts = is->audio_clock - (double)(2 * is->audio_hw_buf_size + is->audio_write_buf_size) / bytes_per_sec;
//    is->audio_current_pts_drift = is->audio_current_pts - audio_callback_time / 1000000.0;

	PyThread_release_lock(player->lock);	
	return 0;
}

static
int paStreamCallback(
	const void *input, void *output,
	unsigned long frameCount,
	const PaStreamCallbackTimeInfo* timeInfo,
	PaStreamCallbackFlags statusFlags,
	void *userData )
{
	player_fillOutStream((PlayerObject*) userData, (uint8_t*) output, frameCount * 2 /* bytes */ * NUMCHANNELS);
	return paContinue;
}

static int player_setqueue(PlayerObject* player, PyObject* queue) {
	Py_XDECREF(player->queue);
	Py_INCREF((PyObject*)player);
	Py_BEGIN_ALLOW_THREADS
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
	player->queue = queue;
	PyThread_release_lock(player->lock);
	Py_END_ALLOW_THREADS
	Py_DECREF((PyObject*)player);
	Py_XINCREF(queue);
	return 0;
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
		   NUMCHANNELS, // numOutputChannels
		   paInt16, // sampleFormat
		   SAMPLERATE, // sampleRate
		   AUDIO_BUFFER_SIZE / 2, // framesPerBuffer,
		   &paStreamCallback,
		   player //void *userData
		   );
		if(ret != paNoError) {
			PyErr_SetString(PyExc_RuntimeError, "Pa_OpenDefaultStream failed");
			if(player->outStream) {
				Pa_CloseStream(player->outStream);
				player->outStream = NULL;
			}
			playing = 0;
		}
	}
	if(playing)
		Pa_StartStream(player->outStream);
	else
		Pa_StopStream(player->outStream);
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
			PyObject* stateObj = PyBool_FromLong(oldplayingstate);
			PyDict_SetItemString(kwargs, "oldState", stateObj);
			Py_DECREF(stateObj);
			stateObj = PyBool_FromLong(playing);
			PyDict_SetItemString(kwargs, "newState", stateObj);
			Py_DECREF(stateObj);
			
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

static
PyObject* player_new(PyTypeObject *subtype, PyObject *args, PyObject *kwds) {
	PlayerObject* player = (PlayerObject*) subtype->tp_alloc(subtype, 0);
	//printf("%p new\n", player);
	return (PyObject*)player;
}

static
int player_init(PyObject* self, PyObject* args, PyObject* kwds) {
	PlayerObject* player = (PlayerObject*) self;
	//printf("%p player init\n", player);

	player->lock = PyThread_allocate_lock();

	player->nextSongOnEof = 1;
	player->volume = 0.9f;
	smoothClip_setX(&player->volumeSmoothClip, 0.95f, 10.0f);
	
	// see also player_setplaying where we init the PaStream (with same params)
	player->audio_tgt.freq = SAMPLERATE;
	player->audio_tgt.fmt = AV_SAMPLE_FMT_S16;
	player->audio_tgt.channels = NUMCHANNELS;
	player->audio_tgt.channel_layout = av_get_default_channel_layout(NUMCHANNELS);
	
	return 0;
}

static
void player_dealloc(PyObject* obj) {
	PlayerObject* player = (PlayerObject*)obj;
	//printf("%p dealloc\n", player);
	
	// TODO: use Py_BEGIN_ALLOW_THREADS etc? what about deadlocks?

	Py_XDECREF(player->dict);
	player->dict = NULL;
	
	Py_XDECREF(player->curSong);
	player->curSong = NULL;

	Py_XDECREF(player->curSongMetadata);
	player->curSongMetadata = NULL;
	
	Py_XDECREF(player->queue);
	player->queue = NULL;

	if(player->outStream) {
		Pa_CloseStream(player->outStream);
		player->outStream = NULL;
	}

	player_closeInputStream(player);
	
	if(player->frame) {
		av_free(player->frame);
		player->frame = NULL;
	}
	
	if(player->swr_ctx) {
		swr_free(&player->swr_ctx);
		player->swr_ctx = NULL;
	}
			
	PyThread_free_lock(player->lock);
	player->lock = NULL;
	
	Py_TYPE(obj)->tp_free(obj);
}

static
PyObject* player_method_seekAbs(PyObject* self, PyObject* arg) {
	PlayerObject* player = (PlayerObject*) self;
	double argDouble = PyFloat_AsDouble(arg);
	if(PyErr_Occurred()) return NULL;
	int ret = 0;
	Py_INCREF(self);
	Py_BEGIN_ALLOW_THREADS
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
	ret = stream_seekAbs(player, argDouble);
	PyThread_release_lock(player->lock);
	Py_END_ALLOW_THREADS
	Py_DECREF(self);
	return PyBool_FromLong(ret == 0);
}

static PyMethodDef md_seekAbs = {
	"seekAbs",
	player_method_seekAbs,
	METH_O,
	NULL
};

static
PyObject* player_method_seekRel(PyObject* self, PyObject* arg) {
	PlayerObject* player = (PlayerObject*) self;
	double argDouble = PyFloat_AsDouble(arg);
	if(PyErr_Occurred()) return NULL;
	int ret = 0;
	Py_INCREF(self);
	Py_BEGIN_ALLOW_THREADS
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
	ret = stream_seekRel(player, argDouble);
	PyThread_release_lock(player->lock);
	Py_END_ALLOW_THREADS
	Py_DECREF(self);
	return PyInt_FromLong(ret == 0);
}

static PyMethodDef md_seekRel = {
	"seekRel",
	player_method_seekRel,
	METH_O,
	NULL
};

static
PyObject* player_method_nextSong(PyObject* self, PyObject* _unused_arg) {
	PlayerObject* player = (PlayerObject*) self;
	int ret = 0;
	Py_INCREF(self);
	Py_BEGIN_ALLOW_THREADS
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
	ret = player_getNextSong(player, 1);
	PyThread_release_lock(player->lock);
	Py_END_ALLOW_THREADS
	Py_DECREF(self);
	if(PyErr_Occurred()) return NULL;
	return PyBool_FromLong(ret == 0);
}

static PyMethodDef md_nextSong = {
	"nextSong",
	player_method_nextSong,
	METH_NOARGS,
	NULL
};

static
PyObject* player_getdict(PlayerObject* player) {
	if(!player->dict) {
		player->dict = PyDict_New();
		if(!player->dict) return NULL;
		// This function is called when we want to ensure that we have a dict,
		// i.e. we requested for it.
		// This is most likely from IPython or so, thus give the developer
		// a list of possible entries.
		PyDict_SetItemString(player->dict, "onSongChange", Py_None);
		PyDict_SetItemString(player->dict, "onSongFinished", Py_None);
		PyDict_SetItemString(player->dict, "onPlayingStateChange", Py_None);
	}
	return player->dict;
}

static
PyObject* player_getattr(PyObject* obj, char* key) {
	PlayerObject* player = (PlayerObject*)obj;
	//printf("%p getattr %s\n", player, key);
	
	if(strcmp(key, "__dict__") == 0) {
		PyObject* dict = player_getdict(player);
		Py_XINCREF(dict);
		return dict;
	}
	
	if(strcmp(key, "__members__") == 0) {
		PyObject* mlist = PyList_New(11);
		PyList_SetItem(mlist, 0, PyString_FromString("queue"));
		PyList_SetItem(mlist, 1, PyString_FromString("playing"));
		PyList_SetItem(mlist, 2, PyString_FromString("curSong"));
		PyList_SetItem(mlist, 3, PyString_FromString("curSongPos"));
		PyList_SetItem(mlist, 4, PyString_FromString("curSongLen"));
		PyList_SetItem(mlist, 5, PyString_FromString("curSongMetadata"));
		PyList_SetItem(mlist, 6, PyString_FromString("seekAbs"));
		PyList_SetItem(mlist, 7, PyString_FromString("seekRel"));
		PyList_SetItem(mlist, 8, PyString_FromString("nextSong"));
		PyList_SetItem(mlist, 9, PyString_FromString("volume"));
		PyList_SetItem(mlist, 10, PyString_FromString("volumeSmoothClip"));
		return mlist;
	}
	
	if(strcmp(key, "queue") == 0) {
		if(player->queue) {
			Py_INCREF(player->queue);
			return player->queue;
		}
		goto returnNone;
	}
	
	if(strcmp(key, "playing") == 0) {
		return PyBool_FromLong(player->playing);
	}
	
	if(strcmp(key, "curSong") == 0) {
		if(player->curSong && player->inStream) { // Note: if we simply check for curSong, we need an additional curSongOpened or so because from the outside, we often want to know if we correctly loaded the current song
			Py_INCREF(player->curSong);
			return player->curSong;
		}
		goto returnNone;
	}
	
	if(strcmp(key, "curSongPos") == 0) {
		if(player->curSong)
			return PyFloat_FromDouble(player->audio_clock);
		goto returnNone;
	}

	if(strcmp(key, "curSongLen") == 0) {
		if(player->curSong && player->curSongLen > 0)
			return PyFloat_FromDouble(player->curSongLen);
		goto returnNone;
	}
	
	if(strcmp(key, "curSongMetadata") == 0) {
		if(player->curSongMetadata) {
			Py_INCREF(player->curSongMetadata);
			return player->curSongMetadata;
		}
		goto returnNone;
	}

	if(strcmp(key, "seekAbs") == 0) {
		return PyCFunction_New(&md_seekAbs, (PyObject*) player);
	}

	if(strcmp(key, "seekRel") == 0) {
		return PyCFunction_New(&md_seekRel, (PyObject*) player);
	}

	if(strcmp(key, "nextSong") == 0) {
		return PyCFunction_New(&md_nextSong, (PyObject*) player);
	}

	if(strcmp(key, "volume") == 0) {
		return PyFloat_FromDouble(player->volume);
	}

	if(strcmp(key, "volumeSmoothClip") == 0) {
		PyObject* t = PyTuple_New(2);
		PyTuple_SetItem(t, 0, PyFloat_FromDouble(player->volumeSmoothClip.x1));
		PyTuple_SetItem(t, 1, PyFloat_FromDouble(player->volumeSmoothClip.x2));
		return t;
	}

	PyObject* dict = player_getdict(player);
	if(dict) { // should always be true...
        Py_INCREF(dict);
        PyObject* res = PyDict_GetItemString(dict, key);
        if (res != NULL) {
            Py_INCREF(res);
            Py_DECREF(dict);
            return res;
        }
        Py_DECREF(dict);		
	}

	PyErr_Format(PyExc_AttributeError, "PlayerObject has no attribute '%.400s'", key);
	return NULL;

returnNone:
	Py_INCREF(Py_None);
	return Py_None;
}

static
int player_setattr(PyObject* obj, char* key, PyObject* value) {
	PlayerObject* player = (PlayerObject*)obj;
	//printf("%p setattr %s %p\n", player, key, value);
	
	if(strcmp(key, "queue") == 0) {
		return player_setqueue(player, value);
	}

	if(strcmp(key, "playing") == 0) {
		return player_setplaying(player, PyObject_IsTrue(value));
	}

	if(strcmp(key, "volume") == 0) {
		if(!PyArg_Parse(value, "f", &player->volume))
			return -1;
		if(player->volume < 0) player->volume = 0;
		if(player->volume > 5) player->volume = 5; // Well, this is made up. But it makes sense to have a limit somewhere...
		return 0;
	}
	
	if(strcmp(key, "volumeSmoothClip") == 0) {
		float x1, x2;
		if(!PyArg_ParseTuple(value, "ff", &x1, &x2))
			return -1;
		smoothClip_setX(&player->volumeSmoothClip, x1, x2);
		return 0;
	}

	PyObject* s = PyString_FromString(key);
	if(!s) return -1;
	int ret = PyObject_GenericSetAttr(obj, s, value);
	Py_XDECREF(s);
	return ret;
}

/*
static PyMemberDef PlayerMembers[] = {
	{"queue", },
};
*/

static PyTypeObject Player_Type = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	"PlayerType",
	sizeof(PlayerObject),	// basicsize
	0,	// itemsize
	player_dealloc,		/*tp_dealloc*/
	0,                  /*tp_print*/
	player_getattr,		/*tp_getattr*/
	player_setattr,		/*tp_setattr*/
	0,                  /*tp_compare*/
	0,					/*tp_repr*/
	0,                  /*tp_as_number*/
	0,                  /*tp_as_sequence*/
	0,                  /*tp_as_mapping*/
	0,					/*tp_hash */
	0, // tp_call
	0, // tp_str
	0, // tp_getattro
	0, // tp_setattro
	0, // tp_as_buffer
	Py_TPFLAGS_HAVE_CLASS, // flags
	"Player type", // doc
	0, // tp_traverse
	0, // tp_clear
	0, // tp_richcompare
	0, // weaklistoffset
	0, // iter
	0, // iternext
	0, // methods
	0, //PlayerMembers, // members
	0, // getset
	0, // base
	0, // dict
	0, // descr_get
	0, // descr_set
	offsetof(PlayerObject, dict), // dictoffset
	player_init, // tp_init
	0, // alloc
	player_new, // new
};


static PyObject *
pyCreatePlayer(PyObject* self) {
	PyTypeObject* type = &Player_Type;
	PyObject *obj = NULL, *args = NULL, *kwds = NULL;
	args = PyTuple_Pack(0);

	obj = type->tp_new(type, args, kwds);
	if(obj == NULL) goto final;
	
	if(type->tp_init && type->tp_init(obj, args, kwds) < 0) {
		Py_DECREF(obj);
		obj = NULL;
	}
	
final:
	Py_XDECREF(args);
	Py_XDECREF(kwds);
	return obj;
}


static PyObject *
pyGetMetadata(PyObject* self, PyObject* args) {
	PyObject* songObj = NULL;
	if(!PyArg_ParseTuple(args, "O:getMetadata", &songObj))
		return NULL;
	
	PyObject* returnObj = NULL;
	PlayerObject* player = (PlayerObject*) pyCreatePlayer(NULL);
	if(!player) goto final;
	player->nextSongOnEof = 0;
	Py_INCREF(songObj);
	player->curSong = songObj;
	player_openInputStream(player);
	
	returnObj = player->curSongMetadata;
	
final:
	if(!returnObj) returnObj = Py_None;
	Py_INCREF(returnObj);
	Py_XDECREF(player);
	return returnObj;
}


static PyObject *
pyCalcAcoustIdFingerprint(PyObject* self, PyObject* args) {
	PyObject* songObj = NULL;
	if(!PyArg_ParseTuple(args, "O:calcAcoustIdFingerprint", &songObj))
		return NULL;
	
	PyObject* returnObj = NULL;
	PlayerObject* player = NULL;
	ChromaprintContext *chromaprint_ctx = NULL;

	player = (PlayerObject*) pyCreatePlayer(NULL);
	if(!player) goto final;
	player->nextSongOnEof = 0;
	player->playing = 1; // otherwise audio_decode_frame() wont read
	Py_INCREF(songObj);
	player->curSong = songObj;
	if(player_openInputStream(player) != 0) goto final;
	if(player->inStream == NULL) goto final;
	
	// fpcalc source for reference:
	// https://github.com/lalinsky/chromaprint/blob/master/examples/fpcalc.c

	chromaprint_ctx = chromaprint_new(CHROMAPRINT_ALGORITHM_DEFAULT);
	chromaprint_start(chromaprint_ctx, SAMPLERATE, NUMCHANNELS);

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
	
	// The following code is loosely adopted from player_fillOutStream().
	unsigned long totalFrameCount = 0;
    while (1) {
		player->audio_buf_index = 0;
		double pts;
		int audio_size = audio_decode_frame(player, &pts);
		if (audio_size < 0)
			break; // probably EOF or so
		else
			player->audio_buf_size = audio_size;

		totalFrameCount += audio_size / NUMCHANNELS / 2 /* S16 */;
		
		if (!chromaprint_feed(chromaprint_ctx, (uint8_t *)player->audio_buf, audio_size / 2)) {
			fprintf(stderr, "ERROR: fingerprint feed calculation failed\n");
			goto final;
		}
    }
	double songDuration = (double)totalFrameCount / SAMPLERATE;
	
	if (!chromaprint_finish(chromaprint_ctx)) {
		fprintf(stderr, "ERROR: fingerprint finish calculation failed\n");
		goto final;
	}

	char* fingerprint = NULL;
	if (!chromaprint_get_fingerprint(chromaprint_ctx, &fingerprint)) {
		fprintf(stderr, "ERROR: unable to calculate fingerprint, get_fingerprint failed\n");
		goto final;
	}

	returnObj = PyTuple_Pack(2,
		PyFloat_FromDouble(songDuration),
		PyString_FromString(fingerprint));

	chromaprint_dealloc(fingerprint);
	
final:
	if(chromaprint_ctx)
		chromaprint_free(chromaprint_ctx);
	if(!returnObj) {
		returnObj = Py_None;
		Py_INCREF(returnObj);
	}
	Py_XDECREF(player);
	return returnObj;
}


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
	
	bmpinfoheader[ 4] = (unsigned char)(       w    );
	bmpinfoheader[ 5] = (unsigned char)(       w>> 8);
	bmpinfoheader[ 6] = (unsigned char)(       w>>16);
	bmpinfoheader[ 7] = (unsigned char)(       w>>24);
	bmpinfoheader[ 8] = (unsigned char)(       h    );
	bmpinfoheader[ 9] = (unsigned char)(       h>> 8);
	bmpinfoheader[10] = (unsigned char)(       h>>16);
	bmpinfoheader[11] = (unsigned char)(       h>>24);
	
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
	if(f < 1.0/6) {
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
}


// idea loosely from:
// http://www.freesound.org/
// https://github.com/endolith/freesound-thumbnailer/blob/master/processing.py

static PyObject *
pyCalcBitmapThumbnail(PyObject* self, PyObject* args, PyObject* kws) {
	PyObject* songObj = NULL;
	int bmpWidth = 400, bmpHeight = 101;
	unsigned char bgR = 100, bgG = bgR, bgB = bgR;
	unsigned char timeR = 170, timeG = timeR, timeB = timeR;
	int timelineSecInterval = 10;
	PyObject* procCallback = NULL;
	static char *kwlist[] = {
		"song", "width", "height",
		"backgroundColor", "timelineColor",
		"timelineSecInterval",
		"procCallback",
		NULL};
	if(!PyArg_ParseTupleAndKeywords(args, kws, "O|ii(bbb)(bbb)iO:calcBitmapThumbnail", kwlist,
		&songObj,
		&bmpWidth, &bmpHeight,
		&bgR, &bgG, &bgB,
		&timeR, &timeG, &timeB,
		&timelineSecInterval,
		&procCallback))
		return NULL;

	char* img = NULL;
	PyObject* bmp = createBitmap24Bpp(bmpWidth, bmpHeight, &img);
	if(!bmp)
		return NULL; // out of memory
		
	RDFTContext* fftCtx = NULL;
	float* samplesBuf = NULL;
	PyObject* returnObj = NULL;
	PlayerObject* player = NULL;
		
	player = (PlayerObject*) pyCreatePlayer(NULL);
	if(!player) goto final;
	player->nextSongOnEof = 0;
	player->playing = 1; // otherwise audio_decode_frame() wont read
	Py_INCREF(songObj);
	player->curSong = songObj;
	if(player_openInputStream(player) != 0) goto final;
	if(player->inStream == NULL) goto final;	
	
	// First count totalFrameCount.
	unsigned long totalFrameCount = 0;
    while (1) {
		player->audio_buf_index = 0;
		double pts;
		int audio_size = audio_decode_frame(player, &pts);
		if (audio_size < 0)
			break; // probably EOF or so
		else
			player->audio_buf_size = audio_size;
		// (uint8_t *)player->audio_buf, audio_size / 2
		
		totalFrameCount += audio_size / NUMCHANNELS / 2 /* S16 */;
    }
	double songDuration = (double)totalFrameCount / SAMPLERATE;

	// Seek back.
	stream_seekAbs(player, 0.0);
	
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
	
	double samplesPerPixel = totalFrameCount / (double)bmpWidth;
	
	unsigned long frame = 0;
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
			player->audio_buf_index = 0;
			double pts;
			int audio_size = audio_decode_frame(player, &pts);
			if (audio_size < 0)
				break; // probably EOF or so
			else
				player->audio_buf_size = audio_size;
			
			for(size_t i = 0; i < audio_size / 2; ++i) {
				int16_t* sampleAddr = (int16_t*) player->audio_buf + i;
				int16_t sample = *sampleAddr; // TODO: endian swap?
				float sampleFloat = sample / ((double) 0x8000);

				if(sampleFloat < peakMin) peakMin = sampleFloat;
				if(sampleFloat > peakMax) peakMax = sampleFloat;

				if(samplesBufIndex < fftSize) {
					samplesBuf[samplesBufIndex] += sampleFloat * freqWindow[samplesBufIndex] * 0.5f /* we do this twice for each channel */;
				}
				if(i % 2 == 1) samplesBufIndex++;
			}

			frame += audio_size / NUMCHANNELS / 2 /* S16 */;
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
		spectralCentroid *= SAMPLERATE;
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
	if(!returnObj) {
		returnObj = Py_None;
		Py_INCREF(returnObj);
	}
	Py_XDECREF(player);
	return returnObj;
}



static PyObject *
pySetFfmpegLogLevel(PyObject* self, PyObject* args) {
	int level = 0;
	if(!PyArg_ParseTuple(args, "i:setFfmpegLogLevel", &level))
		return NULL;
	
	av_log_set_level(level);

	Py_INCREF(Py_None);
	return Py_None;
}


static PyMethodDef module_methods[] = {
	{"createPlayer",	(PyCFunction)pyCreatePlayer,	METH_NOARGS,	"creates new player"},
    {"getMetadata",		pyGetMetadata,	METH_VARARGS,	"get metadata for Song"},
    {"calcAcoustIdFingerprint",		pyCalcAcoustIdFingerprint,	METH_VARARGS,	"calculate AcoustID fingerprint for Song"},
    {"calcBitmapThumbnail",		(PyCFunction)pyCalcBitmapThumbnail,	METH_VARARGS|METH_KEYWORDS,	"calculate bitmap thumbnail for Song"},
    {"setFfmpegLogLevel",		pySetFfmpegLogLevel,	METH_VARARGS,	"set FFmpeg log level (av_log_set_level)"},
	{NULL,				NULL}	/* sentinel */
};

PyDoc_STRVAR(module_doc,
"FFmpeg player.");

static PyObject* EventClass = NULL;

static void init() {
	PaError ret = Pa_Initialize();
	if(ret != paNoError)
		Py_FatalError("PortAudio init failed");
	
	//#ifndef DEBUG
	av_log_set_level(0);
	//#endif
	avcodec_register_all();
	av_register_all();
	
	PyEval_InitThreads();
}


PyMODINIT_FUNC
initffmpeg(void)
{
	//printf("initffmpeg\n");
	init();
    if (PyType_Ready(&Player_Type) < 0)
        Py_FatalError("Can't initialize player type");
	PyObject* m = Py_InitModule3("ffmpeg", module_methods, module_doc);
	if(!m) {
        Py_FatalError("Can't initialize ffmpeg module");
		return;
	}
	
	if(EventClass == NULL) {
		PyObject* classDict = PyDict_New();
		assert(classDict);
		PyObject* className = PyString_FromString("Event");
		assert(className);
		EventClass = PyClass_New(NULL, classDict, className);
		assert(EventClass);
		Py_XDECREF(classDict); classDict = NULL;
		Py_XDECREF(className); className = NULL;
	}
	
	if(EventClass) {
		Py_INCREF(EventClass);
		PyModule_AddObject(m, "Event", EventClass); // takes the ref
	}
	
	
}
