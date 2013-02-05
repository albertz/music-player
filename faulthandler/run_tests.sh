#!/bin/bash
for VERSION in 2.5 2.6 2.7 3.1 3.2; do
    PYTHON=$(which "python$VERSION")
    if [ $? -ne 0 ]; then
        echo "skip python$VERSION (missing)"
        continue
    fi
    echo "==== Test Python $VERSION ===="
    "$PYTHON" setup.py build || exit $?
    set -x
    PYTHONPATH=$(ls -d build/lib.*-$VERSION) "$PYTHON" tests.py || exit $?
done
