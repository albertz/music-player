// ffmpeg_player.cpp
// part of MusicPlayer, https://github.com/albertz/music-player
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"

#include <stdio.h>
#include <string.h>

// For setting the thread priority to realtime on MacOSX.
#ifdef __APPLE__
#include <mach/mach_init.h>
#include <mach/thread_policy.h>
#include <mach/thread_act.h> // the doc says mach/sched.h but that seems outdated...
#include <pthread.h>
#include <mach/mach_error.h>
#include <mach/mach_time.h>
#endif
static void setRealtime();


#define SAMPLERATE 44100
#define NUMCHANNELS 2


bool PlayerObject::getNextSong(bool skipped) {
	PlayerObject* player = this;
	
	// We must hold the player lock here.
	bool ret = false;
	bool errorOnOpening = false;
	PyGILState_STATE gstate;
	gstate = PyGILState_Ensure();
	
	PyObject* oldSong = player->curSong;
	player->curSong = NULL;
	
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
	
	if(!player->openInStream()) {
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
	
	// make callback onSongChange
	if(player->dict) {
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
	Py_XDECREF(oldSong);
	PyGILState_Release(gstate);
	return ret;
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

static
PyObject* player_new(PyTypeObject *subtype, PyObject *args, PyObject *kwds) {
	PlayerObject* player = (PlayerObject*) subtype->tp_alloc(subtype, 0);
	new (player) PlayerObject();
	//printf("%p new\n", player);
	return (PyObject*)player;
}



void PlayerObject::setAudioTgt(int samplerate, int numchannels) {
	if(this->playing) return;
	// we must reopen the output stream
	this->resetBuffers();
	
	// TODO: error checkking for samplerate or numchannels?
	// No idea how to check what libswresample supports.
	
	// see also player_setplaying where we init the PaStream (with same params)
	this->outSamplerate = samplerate;
	this->outNumChannels = numchannels;
}

static
int player_init(PyObject* self, PyObject* args, PyObject* kwds) {
	PlayerObject* player = (PlayerObject*) self;
	//printf("%p player init\n", player);
		
	player->nextSongOnEof = 1;
	player->skipPyExceptions = 1;
	player->needRealtimeReset = false;
	player->volume = 0.9f;
	player->volumeSmoothClip.setX(0.95f, 10.0f);
	
	player->setAudioTgt(SAMPLERATE, NUMCHANNELS);
	
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
	
	player->outStream.reset();
	player->inStream.reset();
	
	player->~PlayerObject();
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
		PyObject* mlist = PyList_New(14);
		PyList_SetItem(mlist, 0, PyString_FromString("queue"));
		PyList_SetItem(mlist, 1, PyString_FromString("playing"));
		PyList_SetItem(mlist, 2, PyString_FromString("curSong"));
		PyList_SetItem(mlist, 3, PyString_FromString("curSongPos"));
		PyList_SetItem(mlist, 4, PyString_FromString("curSongLen"));
		PyList_SetItem(mlist, 5, PyString_FromString("curSongMetadata"));
		PyList_SetItem(mlist, 6, PyString_FromString("curSongGainFactor"));
		PyList_SetItem(mlist, 7, PyString_FromString("seekAbs"));
		PyList_SetItem(mlist, 8, PyString_FromString("seekRel"));
		PyList_SetItem(mlist, 9, PyString_FromString("nextSong"));
		PyList_SetItem(mlist, 10, PyString_FromString("volume"));
		PyList_SetItem(mlist, 11, PyString_FromString("volumeSmoothClip"));
		PyList_SetItem(mlist, 12, PyString_FromString("outSamplerate"));
		PyList_SetItem(mlist, 13, PyString_FromString("outNumChannels"));
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
	
	if(strcmp(key, "curSongGainFactor") == 0) {
		if(player->curSong)
			return PyFloat_FromDouble(player->curSongGainFactor);
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
	
	if(strcmp(key, "outSamplerate") == 0) {
		return PyInt_FromLong(player->outSamplerate);
	}
	
	if(strcmp(key, "outNumChannels") == 0) {
		return PyInt_FromLong(player->outNumChannels);
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
	
	if(strcmp(key, "curSongGainFactor") == 0) {
		if(!PyArg_Parse(value, "f", &player->curSongGainFactor))
			return -1;
		return 0;
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
		player->volumeSmoothClip.setX(x1, x2);
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
		player->setAudioTgt(freq, player->outNumChannels);
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
		player->setAudioTgt(player->outSamplerate, numchannels);
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
	0, // alloc
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




#ifdef __APPLE__
// https://developer.apple.com/library/mac/#documentation/Darwin/Conceptual/KernelProgramming/scheduler/scheduler.html
// Also, from Google Native Client, osx/nacl_thread_nice.c has some related code.
// Or, from Google Chrome, platform_thread_mac.mm.
void setRealtime() {
	kern_return_t ret;
	thread_port_t threadport = pthread_mach_thread_np(pthread_self());
	
	thread_extended_policy_data_t policy;
	policy.timeshare = 0;
	ret = thread_policy_set(threadport,
							THREAD_EXTENDED_POLICY,
							(thread_policy_t)&policy,
							THREAD_EXTENDED_POLICY_COUNT);
	if(ret != KERN_SUCCESS) {
		fprintf(stderr, "setRealtime() THREAD_EXTENDED_POLICY failed: %d, %s\n", ret, mach_error_string(ret));
		return;
	}
	
	thread_precedence_policy_data_t precedence;
	precedence.importance = 63;
	ret = thread_policy_set(threadport,
							THREAD_PRECEDENCE_POLICY,
							(thread_policy_t)&precedence,
							THREAD_PRECEDENCE_POLICY_COUNT);
	if(ret != KERN_SUCCESS) {
		fprintf(stderr, "setRealtime() THREAD_PRECEDENCE_POLICY failed: %d, %s\n", ret, mach_error_string(ret));
		return;
	}
	
	mach_timebase_info_data_t tb_info;
	mach_timebase_info(&tb_info);
	double timeFact = ((double)tb_info.denom / (double)tb_info.numer) * 1000000;
	
	thread_time_constraint_policy_data_t ttcpolicy;
	ttcpolicy.period = 2.9 * timeFact; // about 128 frames @44.1KHz
	ttcpolicy.computation = 0.75 * 2.9 * timeFact;
	ttcpolicy.constraint = 0.85 * 2.9 * timeFact;
	ttcpolicy.preemptible = 1;
	
	ret = thread_policy_set(threadport,
							THREAD_TIME_CONSTRAINT_POLICY,
							(thread_policy_t)&ttcpolicy,
							THREAD_TIME_CONSTRAINT_POLICY_COUNT);
	if(ret != KERN_SUCCESS) {
		fprintf(stderr, "setRealtime() THREAD_TIME_CONSTRAINT_POLICY failed: %d, %s\n", ret, mach_error_string(ret));
		return;
	}
}
#else
void setRealtime() {} // not implemented yet
#endif


