# This builds the main app wrapper.
# Note that we have .qmake.conf in the root with more options.

TEMPLATE = app
TARGET = MusicPlayer
DESTDIR = $$top_builddir

HEADERS += $$files(*.hpp)
SOURCES += $$files(*.cpp)

# We don't need/link Qt at this point.
CONFIG -= qt

mac {

	OBJECTIVE_SOURCES += $$files(*.mm)

	# We don't have a qmake build for it. It's build via Xcode.
	# Just check its existence.
	pylibpath = $$top_srcdir/python-embedded/build/Release/Python.dylib
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

	AppSignature = AZMP # Application signature (4 characters)

	varlist=""
	# Note on $$enumerate_vars(): it's not available in older qmake,
	# it would give us *way* too much and it would even not get us the
	# relevant variables.
	for(var, $$list( \
			top_srcdir top_builddir TARGET PWD \
			AppSignature QMAKE_MACOSX_DEPLOYMENT_TARGET)) {
		eval( varlist += $$quote($$var=\$\$$$var) " " )
	}

	PythonDylib.files = $$pylibpath
	PythonDylib.path = Contents/MacOS
	QMAKE_BUNDLE_DATA += PythonDylib
	
	PythonBaseDir = $$top_srcdir/python-embedded/pylib
	PythonBase.files = $$PythonBaseDir/pylib.zip $$PythonBaseDir/exec $$PythonBaseDir/pyconfig.h
	PythonBase.path = Contents/Resources/pylib
	QMAKE_BUNDLE_DATA += PythonBase

	# Contents/Info.plist
	MusicPlayer_InfoPlistFile = $$top_srcdir/mac/MusicPlayer/MusicPlayer-Info.plist
	Info_plist.target = Info.plist
	Info_plist.depends = $$MusicPlayer_InfoPlistFile $${DESTDIR}/$${TARGET}.app/Contents/Info.plist
	Info_plist.commands = @$(DEL_FILE) $${DESTDIR}/$${TARGET}.app/Contents/Info.plist$$escape_expand(\\n\\t) \
		$${PWD}/mac_xcode_InfoPlistFilter.py -in $$MusicPlayer_InfoPlistFile -out $${DESTDIR}/$${TARGET}.app/Contents/Info.plist -qmake $$varlist
	QMAKE_EXTRA_TARGETS += Info_plist	
	PRE_TARGETDEPS += $$Info_plist.target

	# Contents/PkgInfo
	PkgInfo.target = PkgInfo
	PkgInfo.depends = $${DESTDIR}/$${TARGET}.app/Contents/PkgInfo
	PkgInfo.commands = @$(DEL_FILE) $$PkgInfo.depends$$escape_expand(\\n\\t) \
		@echo "APPL$$AppSignature" > $$PkgInfo.depends
	QMAKE_EXTRA_TARGETS += PkgInfo
	PRE_TARGETDEPS += $$PkgInfo.target

	# App bundle icon
	ICON = ../icon.icns

	app_bundle_setup.target = .app_bundle_setup
	app_bundle_setup.commands = ../mac/MusicPlayer/build-copyScript.py -qmake $$varlist
	QMAKE_EXTRA_TARGETS += app_bundle_setup
	POST_TARGETDEPS += $$app_bundle_setup.target
}



