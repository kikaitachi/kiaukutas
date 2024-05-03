#!/bin/bash

set -e

build_dir=build
if [ ! -d "${build_dir}" ]; then
  cmake -B "${build_dir}" -G Ninja
fi

cmake --build "${build_dir}"

web_build_dir=$(mktemp -d)

( cd cad && freecad -c parts.py "${web_build_dir}" || true )

tar czf ui/resources.tar.gz robot.urdf -C "${web_build_dir}" .

rm -rf "${web_build_dir}"
