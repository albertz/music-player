# Technical

## Reduce Python

* Minimize Python modules usage. Write some code to list all used modules (and objects).
* Remove GIL. We will use only some small subset of objects anyway (dict, set, string, int, ...). Make reference counter atomic.
* Support memory snapshot after module loading. Needs some tracking about system state dependency. E.g. should track which files are read and whether they changed.

## Trace Python

* For code that is triggered by a GUI event (e.g. click): Trace all further Python calls. I want to know how long it takes until the GUI becomes responsible again and why it takes so long. Also record any spawned threads / subtasks.

## Exclusive access (hog mode)

* It means to send the raw data exclusively over the line (to the DA converter).
* Some players such as [BitPerfect](http://bitperfectsound.blogspot.de/p/hog-mode.html), [Decible](http://sbooth.org/Decibel/), [Pure Music](http://www.channld.com/puremusic/), [audirvana](https://code.google.com/p/audirvana/) support that. This player should too.
* [Paper: OSX Playback Integer Mode](http://www.amr-audio.co.uk/large_image/MAC%20OSX%20audio%20players%20&%20Integer%20Mode.pdf)


