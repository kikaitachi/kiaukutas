# kiaukutas

[![Last build result](https://github.com/kikaitachi/kiaukutas/workflows/CI/badge.svg)](https://github.com/kikaitachi/kiaukutas/actions)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

## BOM

| Quantity | Description |
| -------: | ----------- |
| [8](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/) | Dynamixel XM430-W350-T |
| [12](https://www.aliexpress.com/item/1005006698491596.html) | Steel tube 5mm OD, 4mm ID, 100mm length |
| [69](https://www.aliexpress.com/item/1005005334158919.html) | Bushing 7mm OD, 5mm ID, 4mm length |
| [44](https://www.aliexpress.com/item/1005006209247166.html) | Flange bushing 5mm OD (7mm flange), 3mm ID, 2.1mm total length (0.6mm flange) |
| [44](https://www.aliexpress.com/item/1005004780963524.html) | Shoulder bolt 3mm diameter, M3 thread, 3mm thread length |
| [44](https://www.aliexpress.com/item/32977174437.html) | M2.5 hexagon nuts |

## Building & running

Install build tools and dependencies:
```bash
sudo apt-get install g++ cmake ninja-build libasound2-dev
```

Build:
```bash
./build.sh
```

Run:
```bash
./run.sh
```

## Credits

This project directly or indirectly uses these open source projects:
* [A Gear module for FreeCAD](https://github.com/looooo/freecad.gears)
* [Advanced Linux Sound Architecture project](https://www.alsa-project.org/alsa-doc/alsa-lib/)
* [CMake](https://cmake.org/cmake/help/git-master/)
* [FreeCAD](https://freecad-python-stubs.readthedocs.io/en/latest/autoapi/)
