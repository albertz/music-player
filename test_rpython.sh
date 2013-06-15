#!/bin/bash

# add yours via checks
RPYTHONDIR=~/Downloads/pypy-2.0.2-src

# compile <file.py> <file.exe>
function compile() {
	export PYTHONPATH=$RPYTHONDIR
	$RPYTHONDIR/rpython/translator/goal/translate.py \
	--batch --output $2 $1
}


compile binstruct.py binstruct.exe
