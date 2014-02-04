# http://qt-project.org/wiki/QMake-top-level-srcdir-and-builddir

TEMPLATE = subdirs
SUBDIRS = .initvars.pro core/musicplayer.pro faulthandler debugger app
app.depends = core faulthandler debugger
