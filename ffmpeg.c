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
	PyObject* queue;
    int playing;
} PlayerObject;

static int player_setqueue(PlayerObject* player, PyObject* queue) {
	Py_XDECREF(player->queue);
	player->queue = queue;
	Py_XINCREF(queue);
	return 0;
}

static int player_setplaying(PlayerObject* player, int playing) {
	player->playing = playing;
	return 0;
}

static
PyObject* player_new(PyTypeObject *subtype, PyObject *args, PyObject *kwds) {
	PlayerObject* player = (PlayerObject*) subtype->tp_alloc(subtype, 0);
	//printf("%p new\n", player);
	player->queue = NULL;
	player->playing = 0;
	return (PyObject*)player;
}

static
void player_dealloc(PyObject* obj) {
	PlayerObject* player = (PlayerObject*)obj;
	//printf("%p dealloc\n", player);
	Py_XDECREF(player->queue);
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
	0, // tp_init
	0, // alloc
	player_new, // new
};

static
int read_packet(void *opaque, uint8_t *buf, int buf_size) {
	
}

static
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
