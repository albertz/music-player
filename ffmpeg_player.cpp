// ffmpeg_player.cpp
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"

#include <stdio.h>
#include <string.h>
#include <boost/bind.hpp>


#define SAMPLERATE 44100
#define NUMCHANNELS 2


bool PlayerObject::getNextSong(bool skipped) {
	PlayerObject* player = this;
	
	// We must hold the player lock here.

	while(getNextSongLock) {
		PyScopedUnlock unlock(player->lock);
		usleep(100);
	}
	getNextSongLock = true;
	
	bool ret = false;
	bool errorOnOpening = false;
	
	PyObject* oldSong = player->curSong;
	player->curSong = NULL;

	{
		PyScopedGIL gstate;
		
		if(player->queue == NULL) {
			PyErr_SetString(PyExc_RuntimeError, "player queue is not set");
			goto final;
		}
		
		// Note: No PyIter_Check because it adds CPython 2.7 ABI dependency when
		// using CPython 2.7 headers. Anyway, just calling PyIter_Next directly
		// is also ok since it will do the check itself.
		
		player->curSong = PyIter_Next(player->queue);
		
		// pass through any Python errors
		if(!player->curSong || PyErr_Occurred())
			goto final;
	}

	{
		if(tryOvertakePeekInStream()) {
			// nothing needs to be done anymore!
			ret = true;
		}
		else if(!player->openInStream()) {
			// This is not fatal, so don't make a Python exception.
			// When we are in playing state, we will just skip to the next song.
			// This can happen if we don't support the format or whatever.
			printf("cannot open input stream\n");
			errorOnOpening = true;
		}
		else if(!player->inStream) {
			// This is strange, player_openInputStream should have returned !=0.
			printf("strange error on open input stream\n");
			errorOnOpening = true;
		}
		else
			// everything fine!
			ret = true;
	}
	
	// make callback onSongChange
	if(player->dict) {
		PyScopedGIL gstate;

		PyObject* onSongChange = PyDict_GetItemString(player->dict, "onSongChange");
		if(onSongChange && onSongChange != Py_None) {
			PyObject* kwargs = PyDict_New();
			assert(kwargs);
			if(oldSong)
				PyDict_SetItemString(kwargs, "oldSong", oldSong);
			else
				PyDict_SetItemString(kwargs, "oldSong", Py_None);
			PyDict_SetItemString(kwargs, "newSong", player->curSong);
			PyDict_SetItemString_retain(kwargs, "skipped", PyBool_FromLong(skipped));
			PyDict_SetItemString_retain(kwargs, "errorOnOpening", PyBool_FromLong(errorOnOpening));
			
			PyObject* retObj = PyEval_CallObjectWithKeywords(onSongChange, NULL, kwargs);
			Py_XDECREF(retObj);
			
			// errors are not fatal from the callback, so handle it now and go on
			if(PyErr_Occurred()) {
				PyErr_Print(); // prints traceback to stderr, resets error indicator. also handles sys.excepthook if it is set (see pythonrun.c, it's not said explicitely in the docs)
			}
			
			Py_DECREF(kwargs);
		}
	}
		
final:
	{
		PyScopedGIL gstate;
		Py_XDECREF(oldSong);
	}

	getNextSongLock = false;

	if(ret) {
		openPeekInStreams();
	} else {
		PyScopedGIUnlock gunlock;
		PyScopedUnlock unlock(this->lock);
		player->inStream.reset();
	}
	return ret;
}




static int player_setqueue(PlayerObject* player, PyObject* queue) {
	Py_XDECREF(player->queue);
	Py_INCREF((PyObject*)player);
	Py_BEGIN_ALLOW_THREADS
	{
		PyScopedLock lock(player->lock);
		player->queue = queue;
	}
	Py_END_ALLOW_THREADS
	Py_DECREF((PyObject*)player);
	Py_XINCREF(queue);
	return 0;
}

static int player_setpeekqueue(PlayerObject* player, PyObject* queue) {
	Py_XDECREF(player->peekQueue);
	Py_INCREF((PyObject*)player);
	Py_BEGIN_ALLOW_THREADS
	{
		PyScopedLock lock(player->lock);
		player->peekQueue = queue;
	}
	Py_END_ALLOW_THREADS
	Py_DECREF((PyObject*)player);
	Py_XINCREF(queue);
	return 0;
}

static
PyObject* player_new(PyTypeObject *subtype, PyObject *args, PyObject *kwds) {
	PlayerObject* player = (PlayerObject*) subtype->tp_alloc(subtype, 0);
	//printf("%p new\n", player);
	return (PyObject*)player;
}

static
PyObject* player_alloc(PyTypeObject *type, Py_ssize_t nitems) {
    PyObject *obj;
    const size_t size = _PyObject_VAR_SIZE(type, nitems+1);
    /* note that we need to add one, for the sentinel */
	
    if (PyType_IS_GC(type))
        obj = _PyObject_GC_Malloc(size);
    else
        obj = (PyObject *)PyObject_MALLOC(size);
	
    if (obj == NULL)
        return PyErr_NoMemory();
	
    memset(obj, '\0', size);
	new ((PlayerObject*) obj) PlayerObject();
	
    if (type->tp_flags & Py_TPFLAGS_HEAPTYPE)
        Py_INCREF(type);
	
    if (type->tp_itemsize == 0)
        PyObject_INIT(obj, type);
    else
        (void) PyObject_INIT_VAR((PyVarObject *)obj, type, nitems);
	
    if (PyType_IS_GC(type))
        _PyObject_GC_TRACK(obj);
    return obj;
}

static
int player_init(PyObject* self, PyObject* args, PyObject* kwds) {
	PlayerObject* player = (PlayerObject*) self;
	//printf("%p player init\n", player);
	
	player->nextSongOnEof = 1;
	player->skipPyExceptions = 1;
	player->volumeAdjustEnabled = true;
	player->volume = 0.9f;
	player->volumeSmoothClip.setX(0.95f, 10.0f);
	player->soundcardOutputEnabled = true;
	
	player->openStreamLock = player->openPeekInStreamsLock = player->getNextSongLock = false;
	
	{
		// We have the Python GIL here. For setAudioTgt, we need the Player lock.
		// For performance reasons, just disable the lock and do it without locking.
		// This is safe because we have the only reference here.
		player->lock.enabled = false;
		player->setAudioTgt(SAMPLERATE, NUMCHANNELS);
		player->lock.enabled = true;
	}
	
	player->workerThread.func = boost::bind(&PlayerObject::workerProc, player, _1, _2);
	
	return 0;
}

static
void player_dealloc(PyObject* obj) {
	PlayerObject* player = (PlayerObject*)obj;
	//printf("%p dealloc\n", player);
		
	// first, destroy any non-python threads
	Py_BEGIN_ALLOW_THREADS
	{
		player->workerThread.stop();
		player->outStream.reset();
	}
	Py_END_ALLOW_THREADS
	
	{
		// we don't need a lock because in dealloc, we have the only ref to this PlayerObject.
		// also, we must not lock it here because we cannot free inStream otherwise.

		player->inStream.reset();
		player->peekInStreams.clear();
		
		Py_XDECREF(player->dict);
		player->dict = NULL;
		
		Py_XDECREF(player->curSong);
		player->curSong = NULL;
		
		Py_XDECREF(player->queue);
		player->queue = NULL;
		
		Py_XDECREF(player->peekQueue);
		player->peekQueue = NULL;
	}

	player->~PlayerObject();
	Py_TYPE(obj)->tp_free(obj);
}


void PlayerObject::setAudioTgt(int samplerate, int numchannels) {
	if(this->playing) return;

	// TODO: error checkking for samplerate or numchannels?
	// No idea how to check what libswresample supports.

	// see also player_setplaying where we init the PaStream (with same params)
	this->outSamplerate = samplerate;
	this->outNumChannels = numchannels;

	// reset the outstream (PortAudio). we must force a reopen.
	this->outStream.reset();

	// we must reopen the output stream
	this->resetBuffers();
}




static
PyObject* player_method_seekAbs(PyObject* self, PyObject* arg) {
	PlayerObject* player = (PlayerObject*) self;
	double argDouble = PyFloat_AsDouble(arg);
	if(PyErr_Occurred()) return NULL;
	int ret = 0;
	Py_INCREF(self);
	Py_BEGIN_ALLOW_THREADS
	{
		PyScopedLock lock(player->lock);
		ret = player->seekAbs(argDouble);
	}
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
	{
		PyScopedLock lock(player->lock);
		ret = player->seekRel(argDouble);
	}
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
	bool ret = false;
	Py_INCREF(self);
	Py_BEGIN_ALLOW_THREADS
	{
		PyScopedLock lock(player->lock);
		ret = player->getNextSong(true);
	}
	Py_END_ALLOW_THREADS
	Py_DECREF(self);
	if(PyErr_Occurred()) return NULL;
	return PyBool_FromLong(ret);
}

static PyMethodDef md_nextSong = {
	"nextSong",
	player_method_nextSong,
	METH_NOARGS,
	NULL
};

static
PyObject* player_method_reloadPeekStreams(PyObject* self, PyObject* _unused_arg) {
	PlayerObject* player = (PlayerObject*) self;
	Py_INCREF(self);
	Py_BEGIN_ALLOW_THREADS
	{
		PyScopedLock lock(player->lock);
		player->openPeekInStreams();
	}
	Py_END_ALLOW_THREADS
	Py_DECREF(self);
	if(PyErr_Occurred())
		// we will consume and handle any error here.
		// player.reloadPeekStreams should not raise any exceptions.
		PyErr_Print();
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef md_reloadPeekStreams = {
	"reloadPeekStreams",
	player_method_reloadPeekStreams,
	METH_NOARGS,
	NULL
};

static
PyObject* player_method_readOutStream(PyObject* self, PyObject* args, PyObject* kws) {
	PlayerObject* player = (PlayerObject*) self;

	long num = player->outSamplerate * player->outNumChannels; // buffer for one second
	static const char *kwlist[] = {"num", NULL};
	if(!PyArg_ParseTupleAndKeywords(args, kws, "|i:readOutStream", (char**)kwlist, &num))
		return NULL;

	if(player->soundcardOutputEnabled) {
		PyErr_SetString(PyExc_RuntimeError, "cannot use readOutStream with soundcardOutputEnabled");
		return NULL;
	}

	if(!player->playing) {
		PyErr_SetString(PyExc_RuntimeError, "cannot use readOutStream while not playing");
		return NULL;
	}
	
	size_t size = num * /* int16_t's */ 2;
	PyObject* buffer = PyString_FromStringAndSize(NULL, size);
	if(!buffer) return NULL;
	memset(PyString_AS_STRING(buffer), 0, size);
	size_t sampleOutNum = 0;

	Py_INCREF(self);
	Py_BEGIN_ALLOW_THREADS
	{
		PyScopedLock lock(player->lock);
		player->readOutStream((int16_t*)PyString_AS_STRING(buffer), num, &sampleOutNum);
	}
	Py_END_ALLOW_THREADS
	Py_DECREF(self);

	// if _PyString_Resize fails, it sets buffer=NULL, so we have the correct error behavior
	_PyString_Resize(&buffer, sampleOutNum * /*int16*/ 2);
	return buffer;
}

static PyMethodDef md_readOutStream = {
	"readOutStream",
	(PyCFunction) player_method_readOutStream,
	METH_VARARGS|METH_KEYWORDS,
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
		const Py_ssize_t C = 20;
		PyObject* mlist = PyList_New(C);
		int i = 0;
		PyList_SetItem(mlist, i++, PyString_FromString("queue"));
		PyList_SetItem(mlist, i++, PyString_FromString("peekQueue"));
		PyList_SetItem(mlist, i++, PyString_FromString("playing"));
		PyList_SetItem(mlist, i++, PyString_FromString("curSong"));
		PyList_SetItem(mlist, i++, PyString_FromString("curSongPos"));
		PyList_SetItem(mlist, i++, PyString_FromString("curSongLen"));
		PyList_SetItem(mlist, i++, PyString_FromString("curSongMetadata"));
		PyList_SetItem(mlist, i++, PyString_FromString("curSongGainFactor"));
		PyList_SetItem(mlist, i++, PyString_FromString("seekAbs"));
		PyList_SetItem(mlist, i++, PyString_FromString("seekRel"));
		PyList_SetItem(mlist, i++, PyString_FromString("nextSong"));
		PyList_SetItem(mlist, i++, PyString_FromString("reloadPeekStreams"));
		PyList_SetItem(mlist, i++, PyString_FromString("readOutStream"));
		PyList_SetItem(mlist, i++, PyString_FromString("volume"));
		PyList_SetItem(mlist, i++, PyString_FromString("volumeSmoothClip"));
		PyList_SetItem(mlist, i++, PyString_FromString("volumeAdjustEnabled"));
		PyList_SetItem(mlist, i++, PyString_FromString("outSamplerate"));
		PyList_SetItem(mlist, i++, PyString_FromString("outNumChannels"));
		PyList_SetItem(mlist, i++, PyString_FromString("soundcardOutputEnabled"));
		PyList_SetItem(mlist, i++, PyString_FromString("nextSongOnEof"));
		assert(i == C);
		return mlist;
	}
	
	if(strcmp(key, "queue") == 0) {
		if(player->queue) {
			Py_INCREF(player->queue);
			return player->queue;
		}
		goto returnNone;
	}

	if(strcmp(key, "peekQueue") == 0) {
		if(player->peekQueue) {
			Py_INCREF(player->peekQueue);
			return player->peekQueue;
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
		if(player->isInStreamOpened())
			return PyFloat_FromDouble(player->curSongPos());
		goto returnNone;
	}
	
	if(strcmp(key, "curSongLen") == 0) {
		if(player->isInStreamOpened() && player->curSongLen() > 0)
			return PyFloat_FromDouble(player->curSongLen());
		goto returnNone;
	}
	
	if(strcmp(key, "curSongMetadata") == 0) {
		if(player->curSongMetadata()) {
			Py_INCREF(player->curSongMetadata());
			return player->curSongMetadata();
		}
		goto returnNone;
	}
	
	if(strcmp(key, "curSongGainFactor") == 0) {
		if(player->isInStreamOpened())
			return PyFloat_FromDouble(player->curSongGainFactor());
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
	
	if(strcmp(key, "reloadPeekStreams") == 0) {
		return PyCFunction_New(&md_reloadPeekStreams, (PyObject*) player);
	}

	if(strcmp(key, "readOutStream") == 0) {
		return PyCFunction_New(&md_readOutStream, (PyObject*) player);
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
	
	if(strcmp(key, "volumeAdjustEnabled") == 0) {
		return PyBool_FromLong(player->volumeAdjustEnabled);
	}
	
	if(strcmp(key, "outSamplerate") == 0) {
		return PyInt_FromLong(player->outSamplerate);
	}
	
	if(strcmp(key, "outNumChannels") == 0) {
		return PyInt_FromLong(player->outNumChannels);
	}

	if(strcmp(key, "soundcardOutputEnabled") == 0) {
		return PyBool_FromLong(player->soundcardOutputEnabled);
	}

	if(strcmp(key, "nextSongOnEof") == 0) {
		return PyBool_FromLong(player->nextSongOnEof);
	}
	
	{
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

	if(strcmp(key, "peekQueue") == 0) {
		return player_setpeekqueue(player, value);
	}
	
	if(strcmp(key, "playing") == 0) {
		PyScopedGIUnlock gunlock;
		PyScopedLock lock(player->lock);
		return player->setPlaying(PyObject_IsTrue(value));
	}
		
	if(strcmp(key, "volume") == 0) {
		if(!PyArg_Parse(value, "f", &player->volume))
			return -1;
		if(player->volume < 0) player->volume = 0;
		if(player->volume > 5) player->volume = 5; // Well, this limit is made up. But it makes sense to have a limit somewhere...
		return 0;
	}
	
	if(strcmp(key, "volumeSmoothClip") == 0) {
		float x1, x2;
		if(!PyArg_ParseTuple(value, "ff", &x1, &x2))
			return -1;
		player->volumeSmoothClip.setX(x1, x2);
		return 0;
	}

	if(strcmp(key, "volumeAdjustEnabled") == 0) {
		player->volumeAdjustEnabled = PyObject_IsTrue(value);
		return 0;
	}
	
	if(strcmp(key, "outSamplerate") == 0) {
		if(player->playing) {
			PyErr_SetString(PyExc_RuntimeError, "cannot set outSamplerate while playing");
			return -1;
		}
		int freq = SAMPLERATE;
		if(!PyArg_Parse(value, "i", &freq))
			return -1;
		{
			PyScopedGIUnlock gunlock;
			PyScopedLock lock(player->lock);
			player->setAudioTgt(freq, player->outNumChannels);
		}
		return 0;
	}
	
	if(strcmp(key, "outNumChannels") == 0) {
		if(player->playing) {
			PyErr_SetString(PyExc_RuntimeError, "cannot set outNumChannels while playing");
			return -1;
		}
		int numchannels = NUMCHANNELS;
		if(!PyArg_Parse(value, "i", &numchannels))
			return -1;
		{
			PyScopedGIUnlock gunlock;
			PyScopedLock lock(player->lock);
			player->setAudioTgt(player->outSamplerate, numchannels);
		}
		return 0;
	}

	if(strcmp(key, "soundcardOutputEnabled") == 0) {
		if(player->playing) {
			PyErr_SetString(PyExc_RuntimeError, "cannot set soundcardOutputEnabled while playing");
			return -1;
		}
		player->soundcardOutputEnabled = PyObject_IsTrue(value);
		return 0;
	}

	if(strcmp(key, "nextSongOnEof") == 0) {
		player->nextSongOnEof = PyObject_IsTrue(value);
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

PyTypeObject Player_Type = {
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
	player_alloc, // alloc
	player_new, // new
};


PyObject *
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




