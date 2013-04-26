#!/bin/zsh

cd "$(dirname "$0")"

#xcodebuild || exit 1


pushd build/Release || exit 1

zipfilename="MusicPlayer-MacApp-$(date "+%Y%m%d")"
i=1
for f in $zipfilename-*.zip; do
	j=$(echo $f | sed -e "s/${zipfilename}-\([0-9]*\)-.*\\.zip/\1/")
	[[ $j -ge $i ]] && i=$(expr $j + 1)
done
zipfilename="$zipfilename-$i-$(git describe --always).zip"

rm MusicPlayer-latest*.zip
zip -9 -r $zipfilename MusicPlayer.app || exit 1
ln -s $zipfilename MusicPlayer-MacApp-latest.zip
popd

rsync -avP build/Release/*.zip albertzeyer@frs.sourceforge.net:/home/frs/project/az-music-player/
