!mac {
	error("I guess this is MacOSX only atm? (Or do you have ObjC?)")
}

# A Python module is named xyz.so, not libxyz.dylib or sth else.
# The following config/template does that.
# From here: http://lists.qt-project.org/pipermail/interest/2012-June/002798.html
CONFIG += plugin no_plugin_name_prefix
TEMPLATE = lib
QMAKE_EXTENSION_SHLIB = so
TARGET = faulthandler
DESTDIR = $$top_builddir

HEADERS = $$files(*.h)
HEADERS += $$files(libffi-src/include/*.h)
OBJECTIVE_SOURCES = $$files(*.m)
SOURCES = $$files(libffi-src/*.c)
SOURCES += $$files(libffi-src/x86/*.c)
SOURCES += $$files(libffi-src/x86/*.S)

CONFIG += thread
CONFIG -= qt

mac {
	INCLUDEPATH += $$top_builddir/python-embedded/CPython/Include
	INCLUDEPATH += libffi-src/include

        QMAKE_LFLAGS += -undefined dynamic_lookup
}
