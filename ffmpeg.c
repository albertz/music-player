// Python module for playing audio

// compile:
// gcc -c ffmpeg.o -I /System/Library/Frameworks/Python.framework/Headers/
// libtool -dynamic -o ffmpeg.so ffmpeg.o -framework Python -lavformat -lavutil -lavcodec -lc

// loosely based on ffplay.c
// https://github.com/FFmpeg/ffmpeg/blob/master/ffplay.c

#include <libavformat/avformat.h>
#include <libswscale/swscale.h>
#include <portaudio.h>
#include <Python.h>
#include <stdio.h>

// Pyton interface:
//	createPlayer() -> player object with:
//		queue: song generator
//		playing: True or False, initially False
//	song object expected interface:
//		url: some url, can be anything


#define AUDIO_BUFFER_SIZE 512

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
	
	// private
	PyObject* curSong;
	AVFormatContext* inStream;
	PaStream* outStream;

	// audio_decode
	//AVPacket flush_pkt;
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
    struct AudioParams audio_src;
    struct AudioParams audio_tgt;
    struct SwrContext *swr_ctx;
//    double audio_current_pts;
//    double audio_current_pts_drift;
	AVFrame *frame;

} PlayerObject;


static int player_read_packet(PlayerObject* player, uint8_t* buf, int buf_size) {
	
	return 0;
}

static int player_seek(PlayerObject* player, int64_t offset, int whence) {
	
	return 0;
}

static int _player_av_read_packet(void *opaque, uint8_t *buf, int buf_size) {
	return player_read_packet((PlayerObject*)opaque, buf, buf_size);
}

static int64_t _player_av_seek(void *opaque, int64_t offset, int whence) {
	return player_seek(opaque, offset, whence);
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
		//...
		
	}
	
	fmt->flags |= AVFMT_FLAG_CUSTOM_IO;
	
	return fmt;
}

static
int player_openInputStream(PlayerObject* player) {
	assert(player->curSong != NULL);
	PyObject* curSong = player->curSong;
	
	AVFormatContext* formatCtx = initFormatCtx(player);
	if(!formatCtx) return -1;
	
	PyObject* urlObj = PyObject_GetAttrString(curSong, "url");
	PyObject* urlStrObj = urlObj ? PyObject_Str(urlObj) : NULL;
	const char* urlStr = urlStrObj ? PyString_AsString(urlStrObj) : "<None>";
	int ret = avformat_open_input(&formatCtx, urlStr, NULL, NULL);
	Py_XDECREF(urlStrObj);
	Py_XDECREF(urlObj);
		
	player->inStream = formatCtx;
	return 0;
}

/* return the wanted number of samples to get better sync if sync_type is video
 * or external master clock */
static int synchronize_audio(PlayerObject *is, int nb_samples)
{
    int wanted_nb_samples = nb_samples;
	return wanted_nb_samples;	
}

/* decode one audio frame and returns its uncompressed size */
static int audio_decode_frame(PlayerObject *is, double *pts_ptr)
{
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
        if ((new_packet = packet_queue_get(&is->audioq, pkt, 1)) < 0)
            return -1;
		
        if (pkt->data == flush_pkt.data) {
            avcodec_flush_buffers(dec);
            flush_complete = 0;
        }
		
        *pkt_temp = *pkt;
		
        /* if update the audio clock with the pts */
        if (pkt->pts != AV_NOPTS_VALUE) {
            is->audio_clock = av_q2d(is->audio_st->time_base)*pkt->pts;
        }
    }
}

static
int player_fillOutStream(PlayerObject* player, uint8_t* stream, int len) {
	if(player->inStream == NULL) {
		if(player_openInputStream(player) != 0) {
			printf("cannot open input stream\n");
			return 0;
		}
	}
	
	PlayerObject* is = player;
    int audio_size, len1;
    int bytes_per_sec;
    int frame_size = av_samples_get_buffer_size(NULL, is->audio_tgt.channels, 1, is->audio_tgt.fmt, 1);
    double pts;
	
   // audio_callback_time = av_gettime();
	
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
	Py_XDECREF(player->queue);
	player->queue = queue;
	Py_XINCREF(queue);
	return 0;
}

static int player_setplaying(PlayerObject* player, int playing) {
	player->playing = playing;
	if(playing)
		Pa_StartStream(player->outStream);
	else
		Pa_StopStream(player->outStream);
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
	printf("%p player init\n", player);

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
		
	return 0;
}

static
void player_dealloc(PyObject* obj) {
	PlayerObject* player = (PlayerObject*)obj;
	//printf("%p dealloc\n", player);
	
	if(player->outStream) {
		Pa_CloseStream(player->outStream);
		player->outStream = NULL;
	}
	
	Py_XDECREF(player->queue);
	player->queue = NULL;
	
	Py_TYPE(obj)->tp_free(obj);
}

static
PyObject* player_getattr(PyObject* obj, char* key) {
	PlayerObject* player = (PlayerObject*)obj;
	//printf("%p getattr %s\n", player, key);
	
	if(strcmp(key, "__members__") == 0) {
		PyObject* mlist = PyList_New(0);
		PyList_Append(mlist, PyString_FromString("queue"));
		PyList_Append(mlist, PyString_FromString("playing"));
		return mlist;
	}
	
	if(strcmp(key, "queue") == 0) {
		if(player->queue) {
			Py_INCREF(player->queue);
			return player->queue;
		}
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	if(strcmp(key, "playing") == 0) {
		return PyBool_FromLong(player->playing);
	}
	
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
