# This builds the main app wrapper.

TEMPLATE = app

mac {
	# We don't need/link Qt at this point.
	CONFIG -= qt

	OBJECTIVE_SOURCES += ../mac/MusicPlayer/main.m

	# We don't have a qmake build for it. It's build via Xcode.
	# Just check its existence.
	pylibpath = ../python-embedded/build/Release/Python.dylib
	!exists( $$pylibpath ) {
		error( "our Python not found" )
	}

	LIBS += -fobjc-arc -fobjc-link-runtime
	LIBS += -framework CoreFoundation -framework Foundation -framework Cocoa
	LIBS += $$pylibpath
}

!mac {
	SOURCES += main.cpp
}


