Music-Player-Daemon backend
===========================

The [`mpdBackend`](https://github.com/albertz/music-player/blob/master/mpdBackend.py) module is a basic implementation of the backend of the [MPD protocol](http://www.musicpd.org/doc/protocol/) for this music player. It means that any [MPD client](http://mpd.wikia.com/wiki/Clients) can connect to this music player and control it.

Note that MPD and this music player have a fundamental different design, thus not all MPD functions can perfectly be mapped as functions in this player. But for many basic functions, good mappings exist.

This backend tries to emulate MPD 0.17.0.

Some of the functions supported so far (high-level list):

* browse files (`lsinfo` command)
* status / play / pause / next / seeking / volume / ...
* current playlist maps to the main queue
* adding to current playlist
* deleting from current playlist 
* search 

More details can be found in the [source](https://github.com/albertz/music-player/blob/master/mpdBackend.py).

