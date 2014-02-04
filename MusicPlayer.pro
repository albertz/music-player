# http://qt-project.org/wiki/QMake-top-level-srcdir-and-builddir

TEMPLATE = subdirs
SUBDIRS = core faulthandler debugger app
app.depends = core faulthandler debugger
