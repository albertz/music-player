
# Existing modules

## `cProfile` module

In stdlib, [official doc](http://docs.python.org/2/library/profile.html#module-cProfile). No mentioning of threads, runs by default only on the main thread.

## `hotshot` module

In stdlib, [official doc](http://docs.python.org/2/library/hotshot.html#module-hotshot).

According to the docs:

> does not yet work well with threads

thus not an option.

## `yappi`

[Homepage](https://code.google.com/p/yappi/), esp. build for multithreaded apps, see [why yappi doc](https://code.google.com/p/yappi/wiki/whyyappi).

Earlier versions didn't save callstack (according to [here](https://rjpower9000.wordpress.com/2013/05/16/thread-profiling-in-python/)).

## `Plop`

By Dropbox, [blog post](https://tech.dropbox.com/2012/07/plop-low-overhead-profiling-for-python/). Every 10ms it saves the stack trace.

