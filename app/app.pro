# This builds the main app wrapper.

TEMPLATE = app

mac {
	SOURCES += ../mac/MusicPlayer/main.m
}

!mac {
	SOURCES += main.cpp
}


