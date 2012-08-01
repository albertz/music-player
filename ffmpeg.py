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
