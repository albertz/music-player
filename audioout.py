# simple audio-out code
# based on pyaudio for now

# to install:
#    easy_install pyaudio

# it might fail on macosx 10.8 because pa_mac_core.h from portaudio
# is broken. add this missing include:
#    #include <CoreAudio/CoreAudio.h>

# maybe, coding some direct native audio out (via ctypes or so)
# would turn out to keep more stable / compatible.
# for mac, see: https://developer.apple.com/library/mac/#documentation/musicaudio/reference/CACoreAudioReference/AudioHardware/CompositePage.html

import pyaudio
pa = pyaudio.PyAudio()
strm = pa.open(
			   format = pyaudio.paInt16,
			   channels = 2, 
			   rate = 44100, 
			   output = True)
from Queue import Queue
strmQueue = Queue(maxsize=1)
def _strmPlayer():
	while True:
		s = strmQueue.get()
		strm.write(s)
		strmQueue.task_done()
from threading import Thread
strmThread = Thread(target=_strmPlayer)
strmThread.daemon = True
strmThread.start()

def play(s):
	if type(s) is list: s = numpy.array(s)
	if type(s) is numpy.ndarray: s = raw_audio_string(s)
	elif type(s) is not str: s = s.getvalue()
	
	strmQueue.put(s)
		
