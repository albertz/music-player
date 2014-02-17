#!/bin/zsh

# Goto project root dir.
cd "$(dirname "$0")"/..
rootdir="$(pwd)"

[ -x /usr/local/bin/git ] && alias git=/usr/local/bin/git
gitrev="$(git show HEAD  --format=format:%h | head -n1)" || exit 1

unset CC
unset CXX
unset CFLAGS
make || exit 1
[ -e MusicPlayer.app ] || { echo "MusicPlayer.app does not exist"; exit 1; }

pushd mac/build/Release || { echo "mac/build/Release does not exist"; exit 1; }

[ "$(find . -name "*-$gitrev.zip")" != "" ] && \
	{ echo "package exists:" *"-$gitrev.zip"; exit 1; }

zipfilename="MusicPlayer-MacApp-$(date "+%Y%m%d")"
i=1
for f in $zipfilename-*.zip(N); do
	j=$(echo $f | sed -e "s/${zipfilename}-\([0-9]*\)-.*\\.zip/\1/")
	[[ $j -ge $i ]] && i=$(expr $j + 1)
done
zipfilename="$zipfilename-$i-$gitrev.zip"

rm MusicPlayer-MacApp-20*.zip
popd

zip -9 -r mac/build/Release/$zipfilename MusicPlayer.app || exit 1

pushd mac/build/Release || { echo "mac/build/Release does not exist"; exit 1; }

dfile="download_macapp_latest.php"
echo "<?php header( 'Location: http://sourceforge.net/projects/az-music-player/files/${zipfilename}/download' ); ?>" >$dfile

popd

rsync -avP build/Release/*.zip albertzeyer@frs.sourceforge.net:/home/frs/project/az-music-player/
rsync -avP build/Release/$dfile albertzeyer,az-music-player@web.sourceforge.net:htdocs/
