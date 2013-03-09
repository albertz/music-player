Compare to MPD
==============

[Music Player Daemon (MPD)](http://musicpd.org) is a music player server which doesn't come with its own GUI but defines an API to control it. Thus, it is only a backend. [Many independent clients / frontends](http://mpd.wikia.com/wiki/Clients) exist.

By that definition, MPD can be very much compared to the core of this Music Player which also doesn't really need a GUI and has several interfaces / APIs to control it - although this player also has some additional optional GUIs and it tries to start one of them by default.

There are some notable differences between this player engine and MPD:

* The main feature of this player is the semi-intelligent infinite main queue. If you didn't specified any further songs explicitely, it will automatically select some for you. It will select higher-liked songs more often and tries to select songs which match the current context with a higher probability.

  There is nothing alike in MPD.

* In MPD, you have several playlists and one of it is the current playlist. A playlist is a finite strictly ordered list of songs. One of the songs of the current playlist is the song which is currently played.

  In this player, there is only one main queue which is always an infinite list of songs. The first entry is always the entry which will be played next. Once it is going to be played, it is removed from the queue - the current song is not part of the queue. The list of recently played songs is completely indepdendent.

  There can be multiple implementations of the main queue. Currently there is only one where you can add songs manually and where it will automatically semi-intelligently select further songs.

* MPD has a strictly integraded music database. MPD can also play arbitrary files but most clients only allow you to add songs to a playlist from the database. Many clients also request the full database on connect.

  In this player, the database is completely optional. It was mostly meant to make searching faster / easier and to store some statistics and extra user information (such as rating).

  The idea is that the user does not manage the music inside the player but manages the music directory the way she/he wants.

  Thus, the database is also designed in a way that file moves / renames aren't problematic and even converts to other formats isn't - the database will still find the songs.

  Also, it is designed with the expectation that the music directory / potential database is way to huge to fully copy a list of all songs to a frontend.

* This player has a ReplayGain analyzing algorithm builtin. It is used automatically to normalize the volume loudness.

  MPD does not have that. Although it can read such information from metatags and apply them. But it fails if these information are not present in the metatags. In practice, if you have songs from many different sources and you don't always analyze all the songs manually with some ReplayGain-tagger, you don't have reliable volume loudness normalization in MPD.

* This player comes with a builtin AcoustID fingerprint generator. This is used by some parts of the player, e.g. for the database to identify songs and also for [MusicBrainz](http://musicbrainz.org) lookups.

Note that this player also has a [basic implementation of the MPD backend protocol](https://github.com/albertz/music-player/blob/master/mpdBackend.readme.md), i.e. you can use this player to some degree as a replacement to MPD. But because of the difference of both players, not all functions of this player engine are available for MPD clients.

