# http://qt-project.org/wiki/QMake-top-level-srcdir-and-builddir

TEMPLATE = subdirs
SUBDIRS = .initvars.pro app core faulthandler debugger _gui guiQt
core.file = core/musicplayer.pro
app.depends = core faulthandler debugger _gui guiQt

mac {
	SUBDIRS += mac
	app.depends += mac
}
