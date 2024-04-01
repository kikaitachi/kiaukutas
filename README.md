# kiaukutas

[![Last build result](https://github.com/kikaitachi/kiaukutas/workflows/CI/badge.svg)](https://github.com/kikaitachi/kiaukutas/actions)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

## Parts

* 8 x [Dynamixel XM430-W350-T](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/)

## Building & running

Install build tools and dependencies:
```
sudo apt-get install g++ cmake ninja-build libasound2-dev
```

Build:
```
./build.sh
```

Run:
```
./run.sh
```

## Credits

This project directly or indirectly uses these open source projects:
* [Advanced Linux Sound Architecture project](https://www.alsa-project.org/alsa-doc/alsa-lib/)
* [CMake](https://cmake.org/cmake/help/git-master/)
* [FreeCAD](https://freecad-python-stubs.readthedocs.io/en/latest/autoapi/)
