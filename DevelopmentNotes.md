Development notes
=================

In here are a few notes about how the code is organized, used concepts, etc.

The main code is all pure Python. It is highly modular. The main playing engine is implemented in C/C++ as a Python module ([`ffmpeg.c`](https://github.com/albertz/music-player/blob/master/ffmpeg.c) and related). It uses [FFmpeg](http://ffmpeg.org/) for decoding and [PortAudio](http://www.portaudio.com/) for output.

A basic principle is to keep the code as simple as possible so that it works. I really want to avoid to overcomplicate things.

The main entry point is [`main`](https://github.com/albertz/music-player/blob/master/main.py). It initializes all the modules. The list of modules is defined in [`State.modules`](https://github.com/albertz/music-player/blob/master/State.py). It contains for example `queue`, `tracker`, `mediakeys`, `gui`, etc.


## Module

A module is controlled by the `utils.Module` class. It refers to a Python module (for example `queue`).

When you start a module (`Module.start`), it starts a new thread and executes the `<modulename>Main` function.

A module is supposed to be reloadable. There is the function `Module.reload` and `State.reloadModules` is supposed to reload all modules. This is mostly only used for/while debugging, though and is probably not stable and not well tested.


## Multithreading and multiprocessing

The whole code makes heavy use of multithreading and multiprocessing. Every module already runs in its own thread. But some modules itself spawn also other threads. The GUI module spawns a new thread for most actions. Heavy calculations should be done in a seperate process so that the GUI and the playing engine (which run both in the main process) are always responsive. There is `utils.AsyncTask` and `utils.asyncCall` for an easy and stable way to do something in a seperate process.


## Playing engine

This is all the [Python native-C module `ffmpeg`](https://github.com/albertz/music-player/blob/master/ffmpeg.c). It provides a player object which represents the player. It needs a generator `player.queue` which yields `Song` objects which provide a way to read file data and seek in the file. See the source code for further detailed reference.

It has the following functionality:

* Plays audio data via the player object. Uses [FFmpeg](http://ffmpeg.org/) for decoding and [PortAudio](http://www.portaudio.com/) for playing.
* Can modify the volume via `player.volume` and also `song.gain` (see source code for details).
* Prevents clipping via a smooth limiting functions which still leaves most sounds unaffected and keeps the dynamic range (see `smoothClip`).
* Can calculate the [ReplayGain](http://www.replaygain.org/) value for a song (see `pyCalcReplayGain`). This is as far as I know the only other implementation of ReplayGain despite the original from [mp3gain](http://mp3gain.sourceforge.net/) ([gain_analysis.c](http://mp3gain.cvs.sourceforge.net/viewvc/mp3gain/mp3gain/gain_analysis.c?view=markup)).
* Can calculate the [AcoustId](http://acoustid.org/) audio fingerprint (see `pyCalcAcoustIdFingerprint`). This one is also used by [MusicBrainz](http://musicbrainz.org/). It uses the [Chromaprint](http://acoustid.org/chromaprint) lib for implementation.
* Provides a simple way to access the song metadata.
* Provides a way to calculate a visual thumbnail for a song which shows the amplitude and the spectral centroid of the frequencies per time (see `pyCalcBitmapThumbnail`). Inspired by [this project](https://github.com/endolith/freesound-thumbnailer/).

The `player` module creates the player object as `State.state.player`. It setups the queue as `queue.queue`. `State.state` provides also some functions to control the player state (`playPause`, `nextSong`).


## GUI

The basic idea is that Python objects are directly represented in the GUI. The main window corresponds to the `State.state` object. Attributes of an object which should be shown in the GUI are marked via the `utils.UserAttrib` decorator. There, you can specify some further information to specify more concretely how an attribute should be displayed.

The GUI has its own module [`gui`](https://github.com/albertz/music-player/blob/master/gui.py). At the moment, only an OSX Cocoa interface ([`guiCocoa`](https://github.com/albertz/music-player/blob/master/guiCocoa.py)) is implemented but a PyQt implementation is planned. There is some special handling for this module as it needs to be run in the main thread in most cases. See `main` for further reference.


## Database

This is the module [`songdb`](https://github.com/albertz/music-player/blob/master/songdb.py).

The database is intended to be an optional system which stores some extra data/statistics about a song and also caches some data which is heavy to calculate (e.g. the fingerprint).

It provides several ways to identify a song:

- By the SHA1 of its path name (relative to the users home dir).
- By the SHA1 of its file.
- By the SHA1 of its AcoustId fingerprint.

This is so that the database stays robust in case the user moves a song file around or changes its metadata.

It uses [SQLite](http://www.sqlite.org/) as its backend. (As it is used mostly as a key/value store with optional external indexing, a complex SQL-like DB is not strictly needed. Earlier, I tried other DBs. For a history, see the [comment in the source](https://github.com/albertz/music-player/blob/master/songdb.py).)

It uses [binstruct](https://github.com/albertz/binstruct) for the serialization.


## Song attribute knowledge system

Some of the initial ideas are presented in [`attribs.txt`](https://github.com/albertz/music-player/blob/master/attribs.txt). This is implemented now mostly for the [`Song` class](https://github.com/albertz/music-player/blob/master/Song.py).

There are several sources where we can get some song attribute from:

- The local `song.__dict__`.
- The database.
- The file metadata (e.g. artist, title, duration).
- Calculate it from the file (e.g. duration, fingerprint, ReplayGain).
- Look it up from some Internet service like MusicBrainz.

To have a generic attribute read interface which captures all different cases, there is the function:

    Song.get(self, attrib, timeout, accuracy)

For each attrib, there might be functions:

- `Song._estimate_<attrib>`, which is supposed to be fast. This is called no matter what the `timeout` is, in case we did not get it from the database.
- `Song._calc_<attrib>`, which is supposed to return the exact value but is heavy to call. If this is needed, it will be executed in a seperate process.

See [`Song`](https://github.com/albertz/music-player/blob/master/Song.py) for further reference.


## Playlist queue

The playlist queue is managed by the [`queue`](https://github.com/albertz/music-player/blob/master/queue.py) module. It has the logic to autofill the queue if there are too less songs in it. The algorithm to automatically select a new song uses the random file queue generator. This is a lazy directory unfolder and random picker, implemented in [`RandomFileQueue`](https://github.com/albertz/music-player/blob/master/RandomFileQueue.py). Every time, it looks at a few songs and selects some song based on

- the song rating,
- the current recently played context (mostly the song genre / tag map).


## Debugging

The module [`stdinconsole`](stdinconsole.py), when started with `--shell`, provides a handy IPython shell to the running application (in addition to the GUI which is still loaded). This is quite helpful to play around. In addition, as said earlier, all the modules are reloadable. I made this so I don't need to interrupt my music playing when playing with the code.
