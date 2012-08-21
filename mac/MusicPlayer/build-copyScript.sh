#!/bin/bash

#  build-copyScript.sh
#  MusicPlayer
#
#  Created by Albert Zeyer on 21.08.12.
#  Copyright (c) 2012 Albert Zeyer. All rights reserved.

test -f "$BUILT_PRODUCTS_DIR/ffmpeg.so" || exit -1

# $PROJECT_DIR : /Users/az/Programmierung/music-player/mac
# $EXECUTABLE_FOLDER_PATH : MusicPlayer.app/Contents/MacOS
# $CONTENTS_FOLDER_PATH : MusicPlayer.app/Contents

PYDIR="$TARGET_BUILD_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH/Python"
mkdir -p "$PYDIR"

cp "$BUILT_PRODUCTS_DIR/ffmpeg.so" "$PYDIR/"
cp "$PROJECT_DIR/../"*.py "$PYDIR/"
#cp "$PROJECT_DIR/"*.py "$PYDIR/"
