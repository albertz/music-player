
TEMPLATE = subdirs

# We need some global variables, such as top_srcdir.
# http://qt-project.org/wiki/QMake-top-level-srcdir-and-builddir
# For Qmake 5, this is easier (via .qmake.conf).
isEmpty(QMAKE_VERSION_5): SUBDIRS += .initvars.pro

SUBDIRS += app core faulthandler debugger _gui guiQt
core.file = core/musicplayer.pro
app.depends = core faulthandler debugger _gui guiQt

mac {
	SUBDIRS += mac
	app.depends += mac
}
