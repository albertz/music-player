# http://qt-project.org/wiki/QMake-top-level-srcdir-and-builddir
# Solution for Qt4.

TEMPLATE=subdirs
SUBDIRS= # don't build anything, we're just generating the .qmake.cache file
QMAKE_SUBSTITUTES += .qmake.cache.in

system(mkdir -p $$MOC_DIR)
system(mkdir -p $$OBJECTS_DIR)
system(mkdir -p $$UI_DIR)
system(mkdir -p $$RCC_DIR)
