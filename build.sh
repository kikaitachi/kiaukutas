#!/bin/bash

set -e

build_dir=build
if [ ! -d "${build_dir}" ]; then
  cmake -B "${build_dir}" -G Ninja
fi

cmake --build "${build_dir}"

rm -rf dist
cp -r web dist
cp cad/XM430-W350-T.stp dist

( cd cad && freecad -c parts.py "../dist" )
