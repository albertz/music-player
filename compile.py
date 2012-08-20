#!/usr/bin/python

import os

def sysExec(cmd):
    print " ".join(cmd)
    r = os.system(" ".join(cmd))
    if r != 0: sys.exit(r)
    
sysExec(["gcc", "-c", "ffmpeg.c", "-I", "/System/Library/Frameworks/Python.framework/Headers/", "-g"])
sysExec(["libtool", "-dynamic", "-o", "ffmpeg.so", "ffmpeg.o",
    "-framework", "Python",
    "-lavformat", "-lavutil", "-lavcodec", "-lswresample", "-lportaudio", "-lc"])
