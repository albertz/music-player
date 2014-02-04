# http://qt-project.org/wiki/QMake-top-level-srcdir-and-builddir

TEMPLATE = subdirs
SUBDIRS = .initvars.pro core faulthandler debugger app
core.file = core/musicplayer.pro
app.depends = core faulthandler debugger
