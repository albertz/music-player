// Python module for playing audio

// compile:
// gcc -c ffmpeg.o -I /System/Library/Frameworks/Python.framework/Headers/
// libtool -dynamic -o ffmpeg.so ffmpeg.o -framework Python -lavformat -lavutil -lavcodec -lswresample -lportaudio -lc

// loosely based on ffplay.c
// https://github.com/FFmpeg/ffmpeg/blob/master/ffplay.c

#include <libavformat/avformat.h>
#include <libswresample/swresample.h>
#include <portaudio.h>
#include <Python.h>
#include <pythread.h>
#include <stdio.h>

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

#define AUDIO_BUFFER_SIZE 2048

typedef struct AudioParams {
    int freq;
    int channels;
    int channel_layout;
    enum AVSampleFormat fmt;
} AudioParams;

typedef struct {
    PyObject_HEAD
	
	// public
	PyObject* queue;
    int playing;
	PyObject* curSong;
	double curSongLen;
	
	// private
	AVFormatContext* inStream;
	PaStream* outStream;
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


static int player_read_packet(PlayerObject* player, uint8_t* buf, int buf_size) {
	//printf("player_read_packet %i\n", buf_size);
	int ret = -1;
	PyObject *readPacketFunc = NULL, *args = NULL, *retObj = NULL;
	
	PyGILState_STATE gstate;
	gstate = PyGILState_Ensure();
	if(player->curSong == NULL) goto final;
	
	readPacketFunc = PyObject_GetAttrString(player->curSong, "readPacket");
	if(readPacketFunc == NULL) goto final;
	
	args = PyTuple_Pack(1, PyInt_FromLong(buf_size));
	retObj = PyObject_CallObject(readPacketFunc, args);
	
	if(!PyString_Check(retObj)) {
		printf("song.readPacket didn't returned a string\n");
		goto final;
	}
	
	ret = PyString_Size(retObj);
	if(ret > buf_size) {
		printf("song.readPacket returned more than buf_size\n");
		ret = buf_size;
	}
	
	memcpy(buf, PyString_AsString(retObj), ret);
	
final:
	Py_XDECREF(retObj);
	Py_XDECREF(args);
	Py_XDECREF(readPacketFunc);
	PyGILState_Release(gstate);
	return ret;
}

static int player_seek(PlayerObject* player, int64_t offset, int whence) {
	//printf("player_seek %lli %i\n", offset, whence);
	int ret = -1;
	PyGILState_STATE gstate;
	gstate = PyGILState_Ensure();
	PyObject *seekRawFunc = NULL, *args = NULL, *retObj = NULL;
	if(player->curSong == NULL) goto final;
	if(whence < 0 || whence > 2) goto final; // AVSEEK_SIZE and others not supported atm
	
	seekRawFunc = PyObject_GetAttrString(player->curSong, "seekRaw");
	if(seekRawFunc == NULL) goto final;

	args = PyTuple_Pack(2, PyLong_FromLongLong(offset), PyInt_FromLong(whence));
	if(args == NULL) goto final;
	retObj = PyObject_CallObject(seekRawFunc, args);
	if(retObj == NULL) goto final;
	
	if(!PyInt_Check(retObj)) goto final;
	ret = PyInt_AsLong(retObj); // NOTE: I don't really know what would be the best strategy in case of overflow...

final:
	Py_XDECREF(retObj);
	Py_XDECREF(args);
	Py_XDECREF(seekRawFunc);
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
	size_t buffer_size = 1024 * 4;
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

/* open a given stream. Return 0 if OK */
static int stream_component_open(PlayerObject *is, AVFormatContext* ic, int stream_index)
{
    AVCodecContext *avctx;
    AVCodec *codec;
    AVDictionaryEntry *t = NULL;
	
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
			
			memset(&is->audio_pkt, 0, sizeof(is->audio_pkt));
			memset(&is->audio_pkt_temp, 0, sizeof(is->audio_pkt_temp));
			//packet_queue_start(&is->audioq);
			//SDL_PauseAudio(0);
			break;
		default:
			printf("stream_component_open: not an audio stream\n");
			return -1;
    }
		
    return 0;
}

static char* objAttrStrDup(PyObject* obj, const char* attrStr) {
	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject* attrObj = PyObject_GetAttrString(obj, attrStr);
	PyObject* attrStrObj = attrObj ? PyObject_Str(attrObj) : NULL;
	char* str = attrStrObj ? PyString_AsString(attrStrObj) : "<None>";
	str = strdup(str);
	Py_XDECREF(attrStrObj);
	Py_XDECREF(attrObj);
	PyGILState_Release(gstate);
	return str;
}

static
int player_openInputStream(PlayerObject* player) {
	char* urlStr = NULL;

	assert(player->curSong != NULL);
	PyObject* curSong = player->curSong;
	
	if(player->inStream) {
		avformat_close_input(&player->inStream);
		player->inStream = NULL;
	}
	
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
	
	// Get the song len: There is formatCtx.duration in AV_TIME_BASE
	// and there is stream.duration in stream time base.
	assert(player->audio_st);
	player->curSongLen = av_q2d(player->audio_st->time_base) * player->audio_st->duration;
	//if(player->curSongLen < 0) { // happens in some cases, e.g. some flac files
	//	player->curSongLen = av_q2d(AV_TIME_BASE_Q) * formatCtx->duration; // doesnt make it better though...
	//}
	if(player->curSongLen < 0)
		player->curSongLen = -1;
	
	player->inStream = formatCtx;
	formatCtx = NULL;
	
final:
	if(urlStr) free(urlStr);
	if(formatCtx) avformat_close_input(&formatCtx);
	if(player->inStream) return 0;
	return -1;
}

static int player_getNextSong(PlayerObject* player) {
	PyGILState_STATE gstate;
	gstate = PyGILState_Ensure();
		
	Py_XDECREF(player->curSong);
	player->curSong = NULL;
	
	if(player->queue == NULL) {
		printf("player queue is not set");
		goto final;
	}
	
	player->curSong = PyIter_Next(player->queue);

	if(player->curSong && player_openInputStream(player) != 0) {
		printf("cannot open input stream\n");
	}

final:
	PyGILState_Release(gstate);
	if(player->curSong && player->inStream) return 0;
	return -1;
}

/* return the wanted number of samples to get better sync if sync_type is video
 * or external master clock */
static int synchronize_audio(PlayerObject *is, int nb_samples)
{
    int wanted_nb_samples = nb_samples;
	return wanted_nb_samples;	
}

// called from player_fillOutStream
/* decode one audio frame and returns its uncompressed size */
static int audio_decode_frame(PlayerObject *is, double *pts_ptr)
{
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
			
            /* if no pts, then compute it */
            pts = is->audio_clock;
            *pts_ptr = pts;
            is->audio_clock += (double)data_size /
			(dec->channels * dec->sample_rate * av_get_bytes_per_sample(dec->sample_fmt));
#ifdef DEBUG
            {
                static double last_clock;
                printf("audio: delay=%0.3f clock=%0.3f pts=%0.3f\n",
                       is->audio_clock - last_clock,
                       is->audio_clock, pts);
                last_clock = is->audio_clock;
            }
#endif
            return resampled_data_size;
        }
		
        /* free the current packet */
        if (pkt->data)
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
				if(eof)
					// skip to next song
					player_getNextSong(is);
				return -1;
			}
			
			if(pkt->stream_index == is->audio_stream)
				break;
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
int player_fillOutStream(PlayerObject* player, uint8_t* stream, int len) {
	// TODO: maybe it is better with NOWAIT to avoid any deadlocks ?
	PyThread_acquire_lock(player->lock, WAIT_LOCK);

	if(player->inStream == NULL) {
		if(player_getNextSong(player) != 0) {
			printf("cannot get next song");
		}
	}
	
	PlayerObject* is = player;
    int audio_size, len1;
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
	player_fillOutStream((PlayerObject*) userData, (uint8_t*) output, frameCount * 2 /* bytes */ * 2 /* stereo */);
	return paContinue;
}

static int player_setqueue(PlayerObject* player, PyObject* queue) {
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
	Py_XDECREF(player->queue);
	player->queue = queue;
	Py_XINCREF(queue);
	PyThread_release_lock(player->lock);
	return 0;
}

static int player_setplaying(PlayerObject* player, int playing) {
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
	player->playing = playing;
	Py_BEGIN_ALLOW_THREADS
	if(playing)
		Pa_StartStream(player->outStream);
	else
		Pa_StopStream(player->outStream);
	Py_END_ALLOW_THREADS
	PyThread_release_lock(player->lock);
	return 0;
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

	PaError ret;
	ret = Pa_OpenDefaultStream(
		&player->outStream,
		0,
		2, // numOutputChannels
		paInt16, // sampleFormat
		44100, // sampleRate
		AUDIO_BUFFER_SIZE / 2, // framesPerBuffer,
		&paStreamCallback,
		player //void *userData
		);
	if(ret != paNoError)
		Py_FatalError("PortAudio open default stream failed");
	
	player->audio_tgt.freq = 44100;
	player->audio_tgt.fmt = AV_SAMPLE_FMT_S16;
	player->audio_tgt.channels = 2;
	player->audio_tgt.channel_layout = av_get_default_channel_layout(2);
	
	return 0;
}

static
void player_dealloc(PyObject* obj) {
	PlayerObject* player = (PlayerObject*)obj;
	//printf("%p dealloc\n", player);
	
	// TODO: use Py_BEGIN_ALLOW_THREADS etc? what about deadlocks?
	
	if(player->outStream) {
		Pa_CloseStream(player->outStream);
		player->outStream = NULL;
	}

	if(player->inStream) {
		avformat_close_input(&player->inStream);
		player->inStream = NULL;
	}
		
	Py_XDECREF(player->queue);
	player->queue = NULL;
	
	PyThread_free_lock(player->lock);
	player->lock = NULL;
	
	Py_TYPE(obj)->tp_free(obj);
}

static
PyObject* player_method_seekAbs(PyObject* self, PyObject* arg) {
	PlayerObject* player = (PlayerObject*) self;
	double argDouble = PyFloat_AsDouble(arg);
	if(PyErr_Occurred()) return NULL;
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
	int ret = stream_seekAbs(player, argDouble);
	PyThread_release_lock(player->lock);
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
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
	int ret = stream_seekRel(player, argDouble);
	PyThread_release_lock(player->lock);
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
	PyThread_acquire_lock(player->lock, WAIT_LOCK);
	int ret = player_getNextSong(player);
	PyThread_release_lock(player->lock);
	return PyBool_FromLong(ret == 0);
}

static PyMethodDef md_nextSong = {
	"nextSong",
	player_method_nextSong,
	METH_NOARGS,
	NULL
};

static
PyObject* player_getattr(PyObject* obj, char* key) {
	PlayerObject* player = (PlayerObject*)obj;
	//printf("%p getattr %s\n", player, key);
	
	if(strcmp(key, "__members__") == 0) {
		PyObject* mlist = PyList_New(0);
		PyList_Append(mlist, PyString_FromString("queue"));
		PyList_Append(mlist, PyString_FromString("playing"));
		PyList_Append(mlist, PyString_FromString("curSong"));
		PyList_Append(mlist, PyString_FromString("curSongPos"));
		PyList_Append(mlist, PyString_FromString("curSongLen"));
		PyList_Append(mlist, PyString_FromString("seekAbs"));
		PyList_Append(mlist, PyString_FromString("seekRel"));
		PyList_Append(mlist, PyString_FromString("nextSong"));
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
		if(player->curSong) {
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

	if(strcmp(key, "seekAbs") == 0) {
		return PyCFunction_New(&md_seekAbs, (PyObject*) player);
	}

	if(strcmp(key, "seekRel") == 0) {
		return PyCFunction_New(&md_seekRel, (PyObject*) player);
	}

	if(strcmp(key, "nextSong") == 0) {
		return PyCFunction_New(&md_nextSong, (PyObject*) player);
	}

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

	return 0;
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
	0, // dictoffset
	player_init, // tp_init
	0, // alloc
	player_new, // new
};


static PyObject *
pyCreatePlayer(PyObject* self, PyObject* arg) {
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


static void init() {
	PaError ret = Pa_Initialize();
	if(ret != paNoError)
		Py_FatalError("PortAudio init failed");
	
	av_log_set_level(0);
	avcodec_register_all();
	av_register_all();
	
	PyEval_InitThreads();
}


static PyMethodDef module_methods[] = {
	{"createPlayer",    pyCreatePlayer,      METH_NOARGS,         "creates new player"},
	{NULL,              NULL}           /* sentinel */
};

PyDoc_STRVAR(module_doc,
"FFmpeg player.");

PyMODINIT_FUNC
initffmpeg(void)
{
	printf("initffmpeg\n");
	init();
    if (PyType_Ready(&Player_Type) < 0)
        Py_FatalError("Can't initialize player type");
	Py_InitModule3("ffmpeg", module_methods, module_doc);
}
