# Other projects

There exists a huge amount of music players. Here is a list of some and other related projects. This list is not meant to be complete - but rather to be interesting in the scope of this project. This means a focus on Open Source, sound quality, platform independence, advanced DJ features, advanced queuing systems, etc.

(I'm open for suggestions but don't expect that I will just add anything here.)



## Music players

### [Amarok](http://amarok.kde.org/)

* Open Source, based on KDE, ports are too limited.
* It was my preferred player on Linux.

### [Clementine](http://www.clementine-player.org/)

* [Open Source](https://code.google.com/p/clementine-player/), forked Amarok, made cross platform.

### [Audacious](http://audacious-media-player.org/)

* Open Source, descendant of XMMS

### [XMMS2](https://xmms2.org/)

* Open Source

### [Music Player Daemon (MPD)](http://www.musicpd.org/)

* Open Source
* daemon, lightweight, seperate clients
* Note that this player is compatible to MPD, i.e. it emulates the MPD server interface, thus MPD clients work with this player.

### [Tomahawk player](http://www.tomahawk-player.org/)

* [Open Source](https://github.com/tomahawk-player/tomahawk) (GPL)
* MacOSX, Windows, Linux

### [Songbird](http://getsongbird.com/)

* Open Source, based on Mozilla XULRunner + GStreamer.
* Too slow / bloated. Huge amount of problems.
* Project dead since 2013?

### [Banshee](http://banshee.fm/)

### [Exaile](http://exaile.org/)

* Open Source, GTK+, Python.
* Music manager + player.

### [Rhythmbox](https://projects.gnome.org/rhythmbox/)

* Open Source, Gnome.

### [QMMP](http://qmmp.ylsoftware.com/)

* Open Source, Qt

### [Quod Libet](https://code.google.com/p/quodlibet/)

* Open Source, GTK+, Python.
* Make playlist by regular expressions.

### [Listen](http://www.listen-project.org/)

* [Open Source](http://sourceforge.net/projects/listengnome/), Gnome.
* Project dead?

### [Deepin Music Player](https://github.com/linuxdeepin/deepin-music-player)

* Open Source, Python, GStreamer

### [Foobnix](https://github.com/foobnix/foobnix)

* Open Source, Python
* CUE, wv, iso support
* 10-band equalizer

### [Decibel](http://decibel.silent-blade.org/)

* Open Source, GTK+.
* Interesting small project. I found it because there is a [same-named proprietary player for OSX](http://sbooth.org/Decibel/) from the same [person](https://github.com/sbooth) who also developed [Play](#play).
* Lightweight and fast.

### [Play](http://sbooth.org/Play/)

* [Open Source](https://github.com/sbooth/Play), MacOSX only, ObjC mostly.

### [audirvana](https://code.google.com/p/audirvana/)

* Open Source earlier, source not available anymore. seems abandoned because they have a commercial Plus version now.
* OSX only.
* "HAL I/O using DAC native physical formats 'Integer Mode' (instead of CoreAudio 32bit float)", "Audio Device exclusive access mode", "Direct sound path, directly to the CoreAudio HAL for pure bit perfect sound".

### [Douban FM Daemon (FMD)](http://hzqtc.github.io/fmd/)

* Open Source, C, mpg123, libao
* very simple, no fading, no gapless, ...
* inspired by MPD

### [Cog](http://cogx.org/)

* [Open Source](http://sourceforge.net/projects/cogosx/), MacOSX
* no update since 2008, latest release is 0.07

### [gmusicbrowser](http://gmusicbrowser.org/)

* Open Source, Perl, GTK+, GStreamer

### [Nulloy](http://nulloy.com/)

* [Open Source](https://github.com/sergey-vlasov/nulloy), C++, Qt, cross-platform (Win, Linux, Mac)
* Waveform progress bar

### [minirok](http://chistera.yi.org/~dato/code/minirok/)

* Open Source, written in Python, Qt, GStreamer
* modelled as a mini-version of Amarok

### [Pimp: Python Interactive Music Player](http://pimplayer.berlios.de/)

* Open Source, written in Python

### [Python Music Player](http://sourceforge.net/projects/music-player/)

* Open Source, PyGTK, enhanced queueing system
* last update from 2005

### [PyMP: Python Music Player](https://code.google.com/p/python-music-player/)

* Open Source, Python, GStreamer

### [The Python Intelligent MP3 Player](http://sourceforge.net/projects/pimp3/)

* Open Source, Python, song ratings + high-rated songs are played more often
* last update from 2001

### [kwplayer](https://github.com/LiuLang/kwplayer)

* Open Source, Python, GStreamer

### [dacapo](http://sourceforge.net/projects/dacapo-player/)

* Open Source, Python, GStreamer, GTK+


## Web-based streaming players

### [CherryMusic](http://www.fomori.org/cherrymusic/)

* [Open Source](https://github.com/devsnd/cherrymusic) (GPL), Python, [CherryPy](http://www.cherrypy.org/), [jPlayer](http://jplayer.org/)
* no advanced player technics like Gapless playback, mixing, etc. (because of web technology)



## Libraries

For comparisons to Python modules which share features of this Python `musicplayer` core module, see at the [homepage of the musicplayer Python module](https://github.com/albertz/music-player-core).

This is a list of some random related libraries.

### [Mutagen](https://code.google.com/p/mutagen/)

* Python module to handle audio metadata.

### [VSXu](http://www.vsxu.com/)

* [Open Source](https://github.com/vovoid/vsxu) (GPL)
* Audio/Music Visualizer
* Embeddable visual programming language, real-time OpenGL graphics

### [sms-tools](https://github.com/MTG/sms-tools)

* Python
* spectral modelling synthesis tools for sound and music applications

### [libao](http://xiph.org/ao/)

* Open Source (GPL; problem for us because we are BSD)
* cross platform audio output library
* supports OSS, ALSA, PulseAudio, esd, MacOSX, Windows, ...
* latest release was 2011

### [PortAudio](http://www.portaudio.com/)

* Open Source (MIT license), cross-platform, input/output library
* currently used by this project

