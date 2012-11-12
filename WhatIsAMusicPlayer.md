What is a music player?
=======================

Sometimes I get asked questions like:

> What does a music player do?
> Isn't it trivial to just play some mp3s?
> What makes a music player better at playing music than some media player like [VLC](http://www.videolan.org/vlc/)?
> Can the audio playback quality really differ between different players?

So, I'll try to answer these questions here now.


## [Resampling](http://en.wikipedia.org/wiki/Resampling_%28audio%29)

The [soundcard](http://en.wikipedia.org/wiki/Sound_card) or the [operating system (OS)](http://en.wikipedia.org/wiki/Operating_system) usually gets [raw PCM data](http://en.wikipedia.org/wiki/Pulse-code_modulation) from an application. It usually internally works with PCM data at 48 kHz or 96 kHz. If you feed it the PCM data at another frequency, it is often able to resample the data automatically.

Audio [CDs](http://en.wikipedia.org/wiki/Compact_Disc) and most MP3s are encoded with 44.1 kHz and thus there is some resampling needed at some point.

Resampling isn't trivial and there is not really a straight-forward way to do it. Thus, different algorithms can result in much different quality.

A simple media player usually doesn't cares about that and leaves the resampling to the OS or has only some simple resampling algorithm.

A music player usually has its own high-quality resampling algorithm.

This project uses [libswresample of FFmpeg](http://ffmpeg.org/doxygen/trunk/libswresample_2resample_8c-source.html).


## [Loudness normalization](http://en.wikipedia.org/wiki/Audio_normalization#Loudness_normalization)

Different songs from different sources often have different volume / loudness.

A media player usually just plays the song as-is.

In a music player, you usually want that all songs are played with about the same loudness so that you don't have to manually frequently change the volume to adopt to the current song.

Many existing music players don't have their own loudness analyzing algorithm. They depend on external software which analyzes your music and saves the volume-change-information in the metatags of your songs. The music player checks for that metadata information and applies the volume change. However, if it stumbles upon a song which misses this metadata information, it will not be able to do the loudness normalization.

Some professional music players such as iTunes have their own analyzing algorithm.

This project also has its own analyzing algorithm which calculates the loudness of a song based on the [ReplayGain specification](http://www.replaygain.org/).


## Avoid [clipping](http://en.wikipedia.org/wiki/Clipping_%28audio%29) issues when incrementing the volume

When you set the volume to more than 100% (which could also theoretically, though rarely happen from the loudness normalization), you might get the case that you get PCM samples which exceeds the maximum value. E.g. assume that a PCM sample value must be between -1 and 1. If you apply the volume change and you get a value `v > 1`, you must make it fit somehow. The simplest variant would be to just use `1` as the value in that case. This is called clipping.

You want to avoid clipping because it results in bad distorted sound.

Via [dynamic range compression](http://en.wikipedia.org/wiki/Dynamic_range_compression), you can get rid of this effect while at the same time have other quality losses and you have the audio data altered.

This project uses a smooth compression variant which is only applied for values above some high threshold. Thus, in most cases, the audio data is not altered at all which is what [audiophiles](http://en.wikipedia.org/wiki/Audiophile) usually want. The compression itself has some nice properties such as that it is always smooth and will never need clipping.


## Equalizer

In some cases, you might want to have an equalizer to alter the sound a bit.


## Switching songs

The switch to the next song when some song is finished can be done in various ways.

The straight-forward way would be to just start the playback of the next song once the old song has hit the end. This is what most simple media players would do (if they have some playlist support at all).

A music player could do some fading, i.e. fading the old song out and at the same time fading the new song in.

A music player could also try to avoid cracking if the song starts/ends abruptly.

Many music players also have support for [gapless playback](http://en.wikipedia.org/wiki/Gapless_playback). Some songs, e.g. coming from an album might have extra information how much pause there should be between them when playing the songs of the album consecutively.


## Skip silence sections of songs

Some songs have some longer silence sections in between them. In some cases, you might want to automatically skip these sections.


## Different sound formats

There is a wide range of sound formats, like MP3, Flac, WMA, Ogg, etc. It is very non-trivial to have support for them all.

This project uses the great [FFmpeg](http://ffmpeg.org/) library which has support for most formats and codecs.


## Intelligent automatic queue

In a music player when you have a big music library, you sometimes just want to play some random music, maybe listen to some songs you haven't heard in a while, randomly listening through your music. Sometimes you want to play some specific songs and when they are finished, it should randomly play further songs which are similar. Maybe you have some songs on your computer you don't like that much and you prefer to listen to music you like more.

Media players as well as many simple music players usually don't have any functionality where you can achieve this.

Some better music players have such things with some limited functionality. For example iTunes has this and calls it iTunes DJ mode. Some other players call this PartyShuffle.

In this project, this is central element - the main queue.


## [Last.fm](http://last.fm)

You might want to track the songs you listened with [Last.fm](http://last.fm) or some similar service (Last.fm calls this scrobbling). Last.fm can generate some interesting statistics about your music taste and make you new suggestions based on this.

This project supports Last.fm scrobbling.


## Song database

Most users have a huge amount of music. It makes sense for a music player to provide a simple and fast way to search in that music library. Also, the music player sometimes wants to save extra information about songs, such as when you lastly played it and how often you played it, etc. Also, you might want to give the user the ability to add some extra information about a song, such as further tags, some notes or some rating.

For all this, you need a database. Media players as well as simple music players usually don't have.

Most more complex music players as well as this project have that.


## Audio fingerprint

An audio fingerprint represents the song. Depending on the properties of the fingerprint, you can compare a song for similarity (based on the similarity of the fingerprint) and search for duplicate songs. Also, there are services like [MusicBrainz](http://musicbrainz.org) where you can query for metadata information such as artist name and title for any given song fingerprint. This makes sense if these information are missing.

This project can calculate the [AcoustId](http://acoustid.org/) fingerprint which is also used by MusicBrainz.


## Visual representation of audio data

You might want to see some visual representation of a song. This project supports that and calculates visual representations which look like this:

![song thumbnail](https://github.com/albertz/music-player/raw/master/song-thumbnail.png)

The color represents the spectral centroid of the sound frequency.


---

If you want to know some more about the internals of this project, read the [development notes](DevelopmentNotes.md).

