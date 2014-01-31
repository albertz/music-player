# http://qt-project.org/wiki/QMake-top-level-srcdir-and-builddir

TEMPLATE = subdirs
SUBDIRS = app core
app.depends = core
