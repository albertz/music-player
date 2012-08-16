// Python module for playing audio

// compile:
// gcc -c ffmpeg.o -I /System/Library/Frameworks/Python.framework/Headers/
// libtool -dynamic -o ffmpeg.so ffmpeg.o -framework Python -lavformat -lavutil -lavcodec -lc

// loosely based on ffplay.c
// https://github.com/FFmpeg/ffmpeg/blob/master/ffplay.c

#include <libavformat/avformat.h>
#include <Python.h>
#include <stdio.h>

// Pyton interface:
//	createPlayer() -> player object with:
//		queue: song generator
//		playing: True or False, initially False

typedef struct {
    PyObject_HEAD
    int x;
} PlayerObject;

void player_dealloc(PyObject* obj) {
	PlayerObject* player = (PlayerObject*)obj;
	printf("%p dealloc\n", player);	
}

PyObject* player_getattr(PyObject* obj, char* key) {
	PlayerObject* player = (PlayerObject*)obj;
	printf("%p getattr %s\n", player, key);
	
	return NULL;
}

int player_setattr(PyObject* obj, char* key, PyObject* value) {
	PlayerObject* player = (PlayerObject*)obj;
	printf("%p setattr %s %p\n", player, key, value);
	
	return 0;
}

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
};

int read_packet(void *opaque, uint8_t *buf, int buf_size) {
	
}

int64_t seek(void *opaque, int64_t offset, int whence) {
	
}

AVIOContext* initIoCtx() {
	size_t buffer_size = 1024 * 4;
	unsigned char* buffer = av_malloc(buffer_size);
	
	AVIOContext* io = avio_alloc_context(
		buffer,
		buffer_size,
		0, // writeflag
		NULL, // opaque
		read_packet,
		NULL, // write_packet
		seek		
	);
	
	return io;
}

AVFormatContext* initFormatCtx() {
	AVFormatContext* fmt = avformat_alloc_context();
	if(!fmt) return NULL;
	
	fmt->pb = initIoCtx();
	if(!fmt->pb) {
		//...
		
	}
	
	fmt->flags |= AVFMT_FLAG_CUSTOM_IO;
	
}


AVFormatContext* openStream() {
	AVFormatContext* formatCtx = initFormatCtx();
	if(!formatCtx) return NULL;
	
//	int ret = avformat_open_input(&formatCtx, url, NULL, NULL);
	return NULL;
}



static PyObject *
pyCreatePlayer(PyObject* self, PyObject* arg) {
    PyObject* obj = _PyObject_New(&Player_Type);
	PyObject_Init(obj, &Player_Type);
	return obj;
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
    if (PyType_Ready(&Player_Type) < 0)
        Py_FatalError("Can't initialize player type");
	Py_InitModule3("ffmpeg", module_methods, module_doc);
}
