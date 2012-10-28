#!/bin/bash

cd "$(dirname "$0")"

pushd build/Release
rm MusicPlayer-latest.zip
zip -9 -r MusicPlayer-latest.zip MusicPlayer.app
popd

ruby github-upload.rb build/Release/MusicPlayer-latest.zip
