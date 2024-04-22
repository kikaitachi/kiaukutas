# kiaukutas

[![Last build result](https://github.com/kikaitachi/kiaukutas/workflows/CI/badge.svg)](https://github.com/kikaitachi/kiaukutas/actions)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

## Parts

* 8 x [Dynamixel XM430-W350-T](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/)
* 12 x [Steel tube 5mm OD, 4mm ID, 100mm length](https://www.aliexpress.com/item/1005006698491596.html)
* 69 x [Bushing 7mm OD, 5mm ID, 4mm length](https://www.aliexpress.com/item/1005005334158919.html)
* 44 x [Flange bushing 5mm OD (7mm flange), 3mm ID, 2.1mm total length (0.6mm flange)](https://www.aliexpress.com/item/1005006209247166.html)

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
