Music player
============

First, if you wonder about what is supposed to be a music player or what makes a music player different from a simple media player, read this: [What is a music player](https://github.com/albertz/music-player/blob/master/WhatIsAMusicPlayer.md)

Annoyed by all existing players because some subset of:

* not open source
* missing sound format ([FLAC](http://flac.sourceforge.net/itunes.html), Ogg, ...)
* bugs ([1](http://bugzilla.songbirdnest.com/show_bug.cgi?id=23640), [2](http://bugzilla.songbirdnest.com/show_bug.cgi?id=25023), [3](http://bugzilla.songbirdnest.com/show_bug.cgi?id=25042), [4](http://bugzilla.songbirdnest.com/show_bug.cgi?id=18503), [5](http://bugzilla.songbirdnest.com/show_bug.cgi?id=18505), [6](http://bugzilla.songbirdnest.com/show_bug.cgi?id=18480), [7](http://bugzilla.songbirdnest.com/show_bug.cgi?id=18478), [8](http://bugzilla.songbirdnest.com/show_bug.cgi?id=25073), [9](http://bugzilla.songbirdnest.com/show_bug.cgi?id=25024), [10](http://bugzilla.songbirdnest.com/show_bug.cgi?id=5975), ...)
* missing output possibility (RAOP, PulseAudio, ...)
* none or too limited intelligent automatic queue (iTunes calls this DJ mode, others call this PartyShuffle)
* no library / database

Features of this player:

* open source (simplified BSD license, see [License.txt](https://github.com/albertz/music-player/blob/master/License.txt))
* simple
* support of most important sound formats
* advanced intelligent automatic queue which is the main mode to play music
* simple music database
* ReplayGain / audio volume normalization
* [Last.fm](http://last.fm) scrobbling
* [AcoustID](http://acoustid.org) fingerprint
* [Gapless playback](http://en.wikipedia.org/wiki/Gapless_playback)
* [MPD backend](https://github.com/albertz/music-player/blob/master/mpdBackend.readme.md)

![MusicPlayer screenshot](https://github.com/albertz/music-player/raw/master/screenshot.png)

About the intelligent automatic queue, what I want (maybe some of these somewhat configurable):

* continuously always add songs when queue becomes too empty
* liked songs more often
* context-based choices, e.g. related songs more likely
* possibility to easily manually add songs to the list
* easy way to restrict to a subset of songs (like a genre, a playlist, a filesystem directory, etc.)

About the database:

* main function: search
* should be fast and optional for playback, i.e. music can be played even when the database is currently not ready for some reason
* should automatically be filled by a filesystem directory
* import like-state from local players like iTunes and also online services like Last.fm

TODO / possible additional missing features:

* BPM determination and clever DJ-like fading
* use tags given by Last.fm (mostly more tags)
* watch music directory for changes (e.g. new files added)
* other GUI implementations

Comparison to other music players:

* [Music Player Daemon (MPD)](https://github.com/albertz/music-player/blob/master/Compare_to_MPD.md)

Installation:

So far, there is a prebuild MacOSX app bundle in the download section which should just work. Otherwise, to get the source working, you need these requirements (e.g. install on MacOSX via Homebrew):

* ffmpeg
* portaudio
* chromaprint

(Debian/Ubuntu: `apt-get install python-dev libsnappy-dev libtool yasm libchromaprint-dev portaudio19-dev libboost-dev`. FFmpeg in Debian/Ubuntu is too old (lacks libswresample), so either do `add-apt-repository ppa:jon-severinsson/ffmpeg && apt-get update && apt-get install libavformat-dev libswresample-dev` or install it from source. [Chromaprint](http://acoustid.org/chromaprint) depends on FFmpeg, so if you have a custom FFmpeg install, you might also want to install that manually. `./configure && make && sudo make install` should work for FFmpeg and PortAudio. You might also want to use `--enable-shared` for FFmpeg. `cmake . && sudo make install` for Chromaprint.)

Then call `./compile.py` to build the Python modules (it will build the Python modules `ffmpeg.so` and `leveldb.so`).

To start the player, just call `./main.py`.

The current GUI is Cocoa only. Additional Qt support is planned. The music player also works without any GUI.

You can also control the player via an interactive Python shell. You can get the shell directly by passing `--shell` to `main.py` or you can use `socketcontrol-interactiveclient.py`. Via the shell, you can do just anything. By default, the shell exports already the two main objects `state` and `queue`. Here some useful actions:

* `import utils`: common imports you might need for the other commands
* `state.curSong`: returns the current song
* `state.player.playing = True`: start playing. or start/stop via `state.playPause()`
* `state.nextSong()`: skips to next song
* `state.queue.shuffle()`: shuffles the queue
* `utils.formatTime(sum([s.get("duration", accuracy=0, fastOnly=True)[0] or 0 for s in queue.queue.list]))`: get the amount of time of all songs in the queue
* `import guiCocoa; reload(guiCocoa)`: reload Cocoa GUI. this might be useful if it crashed (which shouldn't happen, though)

You can use `dir` to get a list of attributes of an object. E.g. `dir(state)` returns list of all `state`-attributes. This might be useful if you want to figure out what you can do. But it might be easier to just look at the source.

Also, don't hesitate to play around with the code. You might be interested in the [automatic queue handling code](https://github.com/albertz/music-player/blob/master/queue.py).

Authors:

* Albert Zeyer, <http://www.az2000.de>: founder of the project, main core, ffmpeg module, etc.
* Bryan Joseph, <http://bryaninspired.com>: some initial ideas about the database

