# This builds the main app wrapper.
# Note that we have .qmake.conf in the root with more options.

TEMPLATE = app
TARGET = MusicPlayer
DESTDIR = $$top_builddir

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

	# We need to handle all the app bundle data. We need to call build-copyScript.py.
	# We need to call it just every time because we cannot really know here
	# whether it is needed or not.
	# Ideally, we would do it after the linking step. However, that is not really
	# possible. See here:
	# http://stackoverflow.com/questions/21528022/qmake-execute-script-after-build
	# Thus, we add a new target. This forces a relink all the time but
	# I don't see any other way.

	varlist=""
	# Note on $$enumerate_vars(): it's not available in older qmake,
	# it would give us *way* too much and it would even not get us the
	# relevant variables.
	for(var, $$list(top_srcdir top_builddir TARGET PWD)) {
		varlist += $$shell_quote($$var=$$val_escape($$var)) " "
	}

	app_bundle_setup.target = .app_bundle_setup
	app_bundle_setup.commands = ../mac/MusicPlayer/build-copyScript.py -qmake $$varlist
	QMAKE_EXTRA_TARGETS += app_bundle_setup
	POST_TARGETDEPS += .app_bundle_setup
}

!mac {
	SOURCES += main.cpp
}


