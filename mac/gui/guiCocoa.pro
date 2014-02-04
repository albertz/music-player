!mac {
	error("I guess this is MacOSX only atm? (Or do you have ObjC + Cocoa?)")
}

# A Python module is named xyz.so, not libxyz.dylib or sth else.
# The following config/template does that.
# From here: http://lists.qt-project.org/pipermail/interest/2012-June/002798.html
CONFIG += plugin no_plugin_name_prefix
TEMPLATE = lib
QMAKE_EXTENSION_SHLIB = so
TARGET = _guiCocoa
DESTDIR = $$top_builddir

HEADERS = $$files(*.h*)
HEADERS += $$files($$top_srcdir/_gui/*.h*)
HEADERS += $$files($$top_srcdir/core/*.h*)
HEADERS += $$files($$top_srcdir/mac/pyobjc-core/Modules/objc/*.h*)
HEADERS += $$files($$top_srcdir/mac/pyobjc-core/libffi-src/include/*.h*)

SOURCES = $$files(*.c*)

CONFIG += thread c++11
CONFIG -= qt
QMAKE_CXXFLAGS += -std=c++11

INCLUDEPATH += $$top_srcdir/_gui
INCLUDEPATH += $$top_srcdir/core
INCLUDEPATH += $$top_srcdir/mac/pyobjc-core/Modules/objc
INCLUDEPATH += $$top_srcdir/mac/pyobjc-core/libffi-src/include

# We cannot use OBJECTIVE_SOURCES because there are a few special cases:
#  - PyObjCBridge.m: no ARC
#  - *.mm: need C++11
#  - *.m + *.mm: ARC

OBJC_SOURCES = $$files(*.m)
OBJC_CFLAGS = -fobjc-arc
ObjC.input = OBJC_SOURCES
ObjC.dependency_type = TYPE_C
ObjC.variable_out = OBJECTS
ObjC.output = ${QMAKE_VAR_OBJECTS_DIR}${QMAKE_FILE_IN_BASE}$${first(QMAKE_EXT_OBJ)}
ObjC.commands = $${QMAKE_CC} $(CCFLAGS) ${QMAKE_OBJECTIVE_CFLAGS} ${OBJC_CFLAGS} $(INCPATH) -c ${QMAKE_FILE_IN} -o ${QMAKE_FILE_OUT}
QMAKE_EXTRA_COMPILERS += ObjC


OBJCXX_SOURCES = $$files(*.mm)
ObjCxx.input = OBJCXX_SOURCES
ObjCxx.dependency_type = TYPE_C
ObjCxx.variable_out = OBJECTS
ObjCxx.output = ${QMAKE_VAR_OBJECTS_DIR}${QMAKE_FILE_IN_BASE}$${first(QMAKE_EXT_OBJ)}
ObjCxx.commands = $${QMAKE_CXX} $(CCFLAGS) $(CXXFLAGS) ${QMAKE_OBJECTIVE_CFLAGS} ${OBJC_CFLAGS} $(INCPATH) -c ${QMAKE_FILE_IN} -o ${QMAKE_FILE_OUT}
QMAKE_EXTRA_COMPILERS += ObjCxx


PyObjCBridgeFile = PyObjCBridge.m
OBJC_SOURCES -= $$PyObjCBridgeFile
PyObjCBridge.input = PyObjCBridgeFile
PyObjCBridge.dependency_type = TYPE_C
PyObjCBridge.variable_out = OBJECTS
PyObjCBridge.output = ${QMAKE_VAR_OBJECTS_DIR}${QMAKE_FILE_IN_BASE}$${first(QMAKE_EXT_OBJ)}
PyObjCBridge.commands = $${QMAKE_CC} $(CCFLAGS) $(INCPATH) -c ${QMAKE_FILE_IN} -o ${QMAKE_FILE_OUT}
QMAKE_EXTRA_COMPILERS += PyObjCBridge


mac {
        QMAKE_LFLAGS += -undefined dynamic_lookup
}
