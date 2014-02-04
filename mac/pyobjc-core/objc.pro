!mac {
	error("I guess this is MacOSX only atm? (Or do you have ObjC?)")
}

# A Python module is named xyz.so, not libxyz.dylib or sth else.
# The following config/template does that.
# From here: http://lists.qt-project.org/pipermail/interest/2012-June/002798.html
CONFIG += plugin no_plugin_name_prefix
TEMPLATE = lib
QMAKE_EXTENSION_SHLIB = so
TARGET = _objc
DESTDIR = $$top_builddir

HEADERS = $$files(Modules/objc/*.h)
HEADERS += $$files(libffi-src/include/*.h)
HEADERS += $$files($$top_builddir/core/*.h*)

OBJECTIVE_SOURCES = $$files(Modules/objc/*.m)

SOURCES = $$files(libffi-src/*.c)
SOURCES += $$files(libffi-src/x86/*.c)
SOURCES += $$files(libffi-src/x86/*.S)

CONFIG += thread
CONFIG -= qt

INCLUDEPATH += libffi-src/include
INCLUDEPATH += $$top_builddir/core

QMAKE_CFLAGS += -DPyObjC_STRICT_DEBUGGING
QMAKE_CFLAGS += -fexceptions 
mac:QMAKE_CFLAGS += -DMACOSX
QMAKE_CFLAGS += -DPyObjC_BUILD_RELEASE=1009
QMAKE_OBJECTIVE_CFLAGS += $$QMAKE_CFLAGS

mac {
        QMAKE_LFLAGS += -undefined dynamic_lookup
}
