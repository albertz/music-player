# Technical

## Reduce Python

* Minimize Python modules usage. Write some code to list all used modules (and objects).
* Remove GIL. We will use only some small subset of objects anyway (dict, set, string, int, ...). Make reference counter atomic.
* Support memory snapshot after module loading. Needs some tracking about system state dependency. E.g. should track which files are read and whether they changed.

## Trace Python

* For code that is triggered by a GUI event (e.g. click): Trace all further Python calls. I want to know how long it takes until the GUI becomes responsible again and why it takes so long. Also record any spawned threads / subtasks.
