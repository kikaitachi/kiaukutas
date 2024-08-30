#!/bin/bash

set -e

download_models=false
rebuild_model=true

while getopts ":ds" opt; do
  case $opt in
    d)
      download_models=true
      ;;
    s)
      rebuild_model=false
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done

llm_model="models/Meta-Llama-3.1-8B-Instruct-IQ4_XS.gguf"

if [ "$download_models" = true ] ; then
  mkdir -p models
  if [ ! -f "${llm_model}" ]; then
    curl -s -S -L https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-IQ4_XS.gguf > "${llm_model}"
  fi
else
  echo "Skipping model download"
fi

freecad_gears_dir=~/.local/share/FreeCAD/Mod/freecad.gears

if [ ! -d "${freecad_gears_dir}" ]; then
  git clone --depth=1 https://github.com/looooo/freecad.gears.git "${freecad_gears_dir}"
  # For compatibility with FreeCAD 0.19 (see https://wiki.freecad.org/Installing_more_workbenches)
  mkdir -p ~/.FreeCAD/Mod
  ln -s "${freecad_gears_dir}" ~/.FreeCAD/Mod/freecad.gears
fi

build_dir=build
if [ ! -d "${build_dir}" ]; then
  cmake -B "${build_dir}" -G Ninja
fi

cmake --build "${build_dir}"

if [ "$rebuild_model" = true ] ; then
  echo "Building URDF file"
  rm -rf dist
  cp -r web dist
  cp cad/XM430-W350-T.stp dist

  (cd cad && freecad -c parts.py "../dist")
else
  echo "Skipping URDF building"
fi
