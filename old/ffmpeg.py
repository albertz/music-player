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
# for reading/decoding, see: https://github.com/FFmpeg/FFmpeg/blob/master/doc/examples/filtering_audio.c


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

print "load dlls"
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

print "parsing avformat.h"    
avformatHeader = cparser.parse(avformatHeader, newState())
print "parsing avcodec.h"    
avcodecHeader = cparser.parse(avcodecHeader, newState())
print "done, registering"

pprint(avformatHeader._errors)
#pprint(avcodecHeader._errors)

import cparser.cwrapper
wrapper = cparser.cwrapper.CWrapper()
wrapper.register(avformatHeader, avformatLib)
wrapper.register(avcodecHeader, avcodecLib)
av = wrapper.wrapped

#print wrapper.get("AVMEDIA_TYPE_AUDIO")
#print avformatHeader.enums["AVMediaType"], avformatHeader.enums["AVMediaType"].body

print wrapper.get("avcodec_decode_audio4").asCCode()
#print wrapper.get("AVCodecContext").asCCode()
print wrapper.get("av_register_all").asCCode()
print wrapper.get("avcodec_register_all").asCCode()
pprint(wrapper.get("AVFrame").body.contentlist)
print av.AVFrame
pprint(av.AVFrame._fields_)

#print wrapper.wrapped.avcodec_decode_audio4

print "call ffmpeg init"
av.avcodec_register_all()
av.av_register_all()

def openFile(fn):
	formatCtx = ctypes.POINTER(av.AVFormatContext)()
	ret = av.avformat_open_input(formatCtx, fn, None, None)
	if ret != 0: raise Exception, "avformat_open_input returned " + str(ret)
	ret = av.avformat_find_stream_info(formatCtx, None)
	if ret != 0: raise Exception, "avformat_find_stream_info returned " + str(ret)

	dec = ctypes.POINTER(av.AVCodec)()
	ret = av.av_find_best_stream(formatCtx, av.AVMEDIA_TYPE_AUDIO, -1, -1, dec, 0)
	if ret < 0: raise Exception, "av_find_best_stream returned " + str(ret)

	print "codec:", dec.contents.id, ctypes.cast(dec.contents.name, ctypes.c_char_p).value, ctypes.cast(dec.contents.long_name, ctypes.c_char_p).value
	
	si = ret
	#print "stream index/num:", si, formatCtx.contents.nb_streams
	stream = formatCtx.contents.streams[si].contents

	# not sure if I'm supposed to alloc or not...
	#codecCtx = av.avcodec_alloc_context3(dec)
	codecCtx = stream.codec # AVCodecContext
	if not codecCtx: raise Exception, "codec is NULL: " + repr(codecCtx)
	ret = av.avcodec_open2(codecCtx, dec, None)
	if ret != 0: raise Exception, "avcodec_open2 returned " + str(ret)
	
	print "channels:", codecCtx.contents.channels
	print "samplerate:", codecCtx.contents.sample_rate
	
	# somehow these are all invalid?
	#print "codec id:", codecCtx.contents.codec_id.value
	#name = av.avcodec_get_name(codecCtx.contents.codec_id.value)
	#name = ctypes.cast(name, ctypes.c_char_p)
	#print "codec name:", name.value
	#print codecCtx.contents.codec_type, codecCtx.contents.codec_type.value, codecCtx.contents.codec_type == av.AVMEDIA_TYPE_AUDIO
	
	# close with av_close_input_file

	resampleCtx = av.av_audio_resample_init(
		2, codecCtx.contents.channels,
		44100, codecCtx.contents.sample_rate,
		av.AV_SAMPLE_FMT_S16, codecCtx.contents.sample_fmt.value,
		16, # filter len
		10, # log2 phase count
		1, # linear
		0.8 # cutoff
	)

	if not resampleCtx: raise Exception, "failed to init resampler"
	# audio_resample_close
	
	packet = av.AVPacket()
	frame = av.AVFrame()
	pprint(dir(frame))

	got_frame = ctypes.c_int()
	numframes = 0
	frameBufferSize = ((av.AVCODEC_MAX_AUDIO_FRAME_SIZE * 3) / 2)
	frameBufferConverted = (ctypes.c_int8 * frameBufferSize)()
	while True:
		ret = av.av_read_frame(formatCtx, packet)
		if ret < 0: break	
		if packet.stream_index != si: continue
		
		av.avcodec_get_frame_defaults(frame)
		ret = av.avcodec_decode_audio4(codecCtx, frame, got_frame, packet)
		if ret < 0:
			print "error on decoding"
			continue		
		if not got_frame: continue
		
		pprint(dir(frame))
		numframes += 1
		dataSize = av.av_samples_get_buffer_size(
			None, codecCtx.contents.channels,
			frame.nb_samples, codecCtx.contents.sample_fmt,
			1).value
		newSamplesDecoded = dataSize / av.av_get_bytes_per_sample(codecCtx.contents.sample_fmt).value
		print frameBufferConverted, frame.data, newSamplesDecoded
		ret = av.audio_resample(resampleCtx, frameBufferConverted, frame.data, newSamplesDecoded)
		if ret < 0:
			print "error on resampling"
			continue
			
	print "numframes:", numframes
	
#av_audio_resample_init

def test():
	fn = "/Users/az/Music/Electronic/One Day_Reckoning Song (Wankelmut Remix) - Asaf Avidan & the Mojos.mp3"
	#fn = "/Users/az/Music/Electronic/Von Paul Kalkbrenner - Aaron.mp3"
	f = openFile(fn)
	

test()
