
# A Python module is named xyz.so, not libxyz.dylib or sth else.
# The following config/template does that.
# From here: http://lists.qt-project.org/pipermail/interest/2012-June/002798.html
CONFIG += plugin no_plugin_name_prefix
TEMPLATE = lib
QMAKE_EXTENSION_SHLIB = so
TARGET = faulthandler
DESTDIR = $$top_builddir

SOURCES = $$files(*.c)

CONFIG += thread
CONFIG -= qt

mac {
        QMAKE_LFLAGS += -undefined dynamic_lookup
}
