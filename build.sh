#!/bin/bash

set -e

freecad_gears_dir=~/.local/share/FreeCAD/Mod/freecad.gears

if [ ! -d "${freecad_gears_dir}" ]; then
  git clone --depth=1 https://github.com/looooo/freecad.gears.git "${freecad_gears_dir}"
fi

build_dir=build
if [ ! -d "${build_dir}" ]; then
  cmake -B "${build_dir}" -G Ninja
fi

cmake --build "${build_dir}"

rm -rf dist
cp -r web dist
cp cad/XM430-W350-T.stp dist

(cd cad && freecad -c parts.py "../dist")
