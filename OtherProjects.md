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

### [Quod Libet](https://code.google.com/p/quodlibet/)

* Open Source, GTK+, Python.
* Make playlist by regular expressions.

### [Listen](http://www.listen-project.org/)

* [Open Source](http://sourceforge.net/projects/listengnome/), Gnome.
* Project dead?

### [Deepin Music Player]((https://github.com/linuxdeepin/deepin-music-player))

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

* Open Source but seems abandoned because they have a commercial Plus version now.
* OSX only.
* "HAL I/O using DAC native physical formats 'Integer Mode' (instead of CoreAudio 32bit float)", "Audio Device exclusive access mode", "Direct sound path, directly to the CoreAudio HAL for pure bit perfect sound".

### [Douban FM Daemon (FMD)](http://hzqtc.github.io/fmd/)

* Open Source, C, mpg123, libao
* very simple, no fading, no gapless, ...
* inspired by MPD



## Web-based streaming players

### [CherryMusic](http://www.fomori.org/cherrymusic/)

* [Open Source](https://github.com/devsnd/cherrymusic) (GPL), Python, [CherryPy](http://www.cherrypy.org/), [jPlayer](http://jplayer.org/)
* no advanced player technics like Gapless playback, mixing, etc. (because of web technology)



## Libraries

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

* Open Source (GPL)
* cross platform audio output library
* supports OSS, ALSA, PulseAudio, esd, MacOSX, Windows, ...
* latest release was 2011

### [PortAudio](http://www.portaudio.com/)

* Open Source (MIT license), cross-platform, input/output library
* currently used by this project

