#!/bin/bash

cd "$(dirname "$0")"

xcodebuild || exit 1

pushd build/Release || exit 1
rm MusicPlayer-latest.zip
zip -9 -r MusicPlayer-latest.zip MusicPlayer.app || exit 1
popd

ruby github-upload.rb build/Release/MusicPlayer-latest.zip
