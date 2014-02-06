
# A Python module is named xyz.so, not libxyz.dylib or sth else.
# The following config/template does that.
# From here: http://lists.qt-project.org/pipermail/interest/2012-June/002798.html
CONFIG += plugin no_plugin_name_prefix
TEMPLATE = lib
QMAKE_EXTENSION_SHLIB = so
TARGET = guiQt
DESTDIR = $$top_builddir

HEADERS = $$files(*.h*)
HEADERS += $$files($$top_srcdir/_gui/*.h*)
HEADERS += $$files($$top_srcdir/core/*.h*)

SOURCES = $$files(*.c*)

CONFIG += thread c++11
QMAKE_CXXFLAGS += -std=c++11

INCLUDEPATH += $$top_srcdir/_gui
INCLUDEPATH += $$top_srcdir/core

mac {
        QMAKE_LFLAGS += -undefined dynamic_lookup
}
