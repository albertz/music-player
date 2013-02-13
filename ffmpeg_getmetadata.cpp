//
//  ffmpeg_getmetadata.cpp
//  MusicPlayer
//
// Copyright (c) 2012, Albert Zeyer, www.az2000.de
// All rights reserved.
// This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

#include "ffmpeg.h"

PyObject*
pyGetMetadata(PyObject* self, PyObject* args) {
	PyObject* songObj = NULL;
	if(!PyArg_ParseTuple(args, "O:getMetadata", &songObj))
		return NULL;
	
	PyObject* returnObj = NULL;
	PlayerObject* player = (PlayerObject*) pyCreatePlayer(NULL);
	if(!player) goto final;
	player->lock.enabled = false;
	player->nextSongOnEof = 0;
	player->skipPyExceptions = 0;
	Py_INCREF(songObj);
	player->curSong = songObj;
	player->openInStream();
	if(PyErr_Occurred()) goto final;
	
	returnObj = player->curSongMetadata();
	
final:
	Py_XINCREF(returnObj);
	Py_XDECREF(player);
	return returnObj;
}
