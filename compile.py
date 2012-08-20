#!/usr/bin/python

import os

def sysExec(cmd):
    print " ".join(cmd)
    os.system(" ".join(cmd))
    
sysExec(["gcc", "-c", "ffmpeg.c", "-I", "/System/Library/Frameworks/Python.framework/Headers/", "-g"])
sysExec(["libtool", "-dynamic", "-o", "ffmpeg.so", "ffmpeg.o",
    "-framework", "Python",
    "-lavformat", "-lavutil", "-lavcodec", "-lswresample", "-lportaudio", "-lc"])
