// Python module for playing audio

// loosely based on ffplay.c
// https://github.com/FFmpeg/ffmpeg/blob/master/ffplay.c

#include <libavformat/avformat.h>
#include <Python.h>

// Pyton interface:
//	createPlayer() -> player object with:
//		queue: song generator
//		playing: True or False, initially False

typedef struct {
    PyObject_HEAD
    double ob_fval;
} PlayerObject;

PyAPI_DATA(PlayerObject) Player_Type;

PyObject* player_getattr(PyObject* obj, char* key) {
    assert(PyType_IsSubtype(type, &Player_Type));
	PlayerObject* player = obj;
	printf("%p getattr %s\n", player, key);
}

int player_setattr(PyObject* obj, char* key, PyObject* value) {
    assert(PyType_IsSubtype(type, &Player_Type));
	PlayerObject* player = obj;
	printf("%p setattr %s %p\n", player, key, value);
	
	return 0;
}

static PyTypeObject Player_Type = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	"PlayerType",
	sizeof(PlayerObject),	// basicsize
	0,	// itemsize
	0,					/*tp_dealloc*/
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


void openStream() {
	AVFormatContext* formatCtx = initFormatCtx();
	if(!formatCtx) return NULL;
	
	int ret = avformat_open_input(&formatCtx, url, NULL, NULL);
	
}



static PyObject *
pyCreatePlayer(PyObject *self, PyObject *arg)
{
}

static PyMethodDef module_methods[] = {
	{"createPlayer",    pyCreatePlayer,      METH_O,         NULL},
	{NULL,              NULL}           /* sentinel */
};

PyDoc_STRVAR(module_doc,
"FFmpeg player.");

PyMODINIT_FUNC
initffmpeg(void)
{
	Py_InitModule3("ffmpeg", module_methods, module_doc);
}
