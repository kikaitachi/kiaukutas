#!/bin/bash

if [ -f "build/bin/kiaukutas" ]; then
  build/bin/kiaukutas "$@"
elif [ -f "build/kiaukutas" ]; then
  build/kiaukutas "$@"
else
  echo "ERROR: can't find binary, did't you forget to run ./build.sh first?"
fi
