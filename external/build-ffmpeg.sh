#!/bin/bash

set -e
cd "$(dirname "$0")"
[ -e ffmpeg/build.sh ] || { echo "ffmpeg/build.sh not found"; exit 1; }

# Force MacOSX 10.6 compatibility.
export SDKROOT=/Developer/SDKs/MacOSX10.6.sdk
[ -e $SDKROOT ] || { echo "$SDKROOT not found"; exit 1; }
export CFLAGS="-mmacosx-version-min=10.6 -DMAC_OS_X_VERSION_MIN_REQUIRED=1060 --sysroot $SDKROOT"
export MACOSX_DEPLOYMENT_TARGET=10.6
./ffmpeg/build.sh -d

