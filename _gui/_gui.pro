
# A Python module is named xyz.so, not libxyz.dylib or sth else.
# The following config/template does that.
# From here: http://lists.qt-project.org/pipermail/interest/2012-June/002798.html
CONFIG += plugin no_plugin_name_prefix
TEMPLATE = lib
QMAKE_EXTENSION_SHLIB = so
TARGET = _gui
DESTDIR = $$top_builddir

SOURCES = $$files(*.cpp)

CONFIG += thread
CONFIG -= qt
QMAKE_CXXFLAGS += -std=c++11

mac {
        QMAKE_LFLAGS += -undefined dynamic_lookup
}
