#!/bin/bash

cd $(dirname $0)

find . -name Makefile\* | \
grep -v "^./core/external/ffmpeg/" | \
grep -v "^./python-embedded/" | \
grep -v "/MusicPlayer.app/" | \
grep -v -E "/Makefile\.(in|am)$" | \
grep -v "/Doc/" | \
{
	while read fn; do
		echo $fn
		rm $fn
	done
}

rm .qmake.cache
