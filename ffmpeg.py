# very simple ffmpeg ctypes wrapper
# supports just enough to play

# load avformat, avcodec

# example code:
# https://github.com/FFmpeg/FFmpeg/blob/master/doc/examples/filtering_audio.c
# http://code.google.com/p/chromium-source-browsing/source/browse/ffmpeg.c?repo=third-party--ffmpeg
# http://dranger.com/ffmpeg/tutorial03.html

# void av_register_all(void);
# void avcodec_register_all(void);

# int avformat_open_input(AVFormatContext **ps, const char *filename, AVInputFormat *fmt, AVDictionary **options);
# fmt can be NULL (for autodetect).
# options can be NULL.
# close with av_close_input_file

# int av_read_play(AVFormatContext *s);

# int av_read_frame(AVFormatContext *s, AVPacket *pkt);
# returns encoded packet
# avcodec_decode_audio4

# int avcodec_decode_audio4(AVCodecContext *avctx, AVFrame *frame,
#                           int *got_frame_ptr, AVPacket *avpkt);

# int av_seek_frame(AVFormatContext *s, int stream_index, int64_t timestamp,
#                   int flags);



# void avformat_close_input(AVFormatContext **s);

# for cparser demo, see: https://github.com/albertz/PySDL/blob/master/SDL/__init__.py

from pprint import pprint
import better_exchook
better_exchook.install()

import os

SearchPaths = ["/usr","/usr/local"]

def searchLib(header, dll):
    for p in SearchPaths:
        fullHeader = p + "/include/" + header
        fullDll = p + "/lib/" + dll
        if os.path.exists(fullHeader) and os.path.exists(fullDll):
            return fullHeader, fullDll
    return None,None
    
avformatHeader,avformatLib = searchLib("libavformat/avformat.h", "libavformat.dylib")
assert avformatHeader
avcodecHeader,avcodecLib = searchLib("libavcodec/avcodec.h", "libavcodec.dylib")
assert avcodecHeader

import ctypes
avformatLib = ctypes.cdll.LoadLibrary(avformatLib)
avcodecLib = ctypes.cdll.LoadLibrary(avcodecLib)

import cparser
def newState():
    parserState = cparser.State()
    parserState.autoSetupSystemMacros()

    oldFindInclude = parserState.findIncludeFullFilename
    def findInclude(filename, local):
        fn = oldFindInclude(filename, local)
        if os.path.exists(fn): return fn
        for p in SearchPaths:
            if os.path.exists(p + "/include/" + filename):
                return p + "/include/" + filename
        return filename
    parserState.findIncludeFullFilename = findInclude

    return parserState
    
avformatHeader = cparser.parse(avformatHeader, newState())
avcodecHeader = cparser.parse(avcodecHeader, newState())

#pprint(avformatHeader._errors)
#pprint(avcodecHeader._errors)

import cparser.cwrapper
wrapper = cparser.cwrapper.CWrapper()
wrapper.register(avformatHeader, avformatLib)
wrapper.register(avcodecHeader, avcodecLib)

print wrapper.get("avcodec_decode_audio4").asCCode()
#print wrapper.get("AVCodecContext").asCCode()
print wrapper.get("av_register_all").asCCode()
print wrapper.get("avcodec_register_all").asCCode()

#print wrapper.wrapped.avcodec_decode_audio4

wrapper.wrapped.av_register_all()
wrapper.wrapped.avcodec_register_all()
