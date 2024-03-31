from FreeCAD import newDocument, Placement, Rotation, Vector
from time import time
from typing import Optional
import FreeCADGui
import Part

start_time = time()

PULLEY_HEIGHT = 4
BRACKET_THICKNESS = 4
MOTOR_LENGTH = 28.5
MOTOR_WIDTH = 46.5

doc = newDocument("kiaukutas")


def cylinder(
    *,
    height: float,
    radius: Optional[float] = None,
    diameter: Optional[float] = None,
    translation: Optional[Vector] = Vector(0, 0, 0),
    rotation: Optional[Rotation] = Rotation(0, 0, 0),
    center=None,
    title: Optional[str] = "cylinder",
):
    result = doc.addObject("Part::Cylinder")
    result.Radius = radius if diameter is None else diameter / 2.0
    result.Height = height
    if center is None:
        result.Placement = Placement(translation, rotation)
    else:
        result.Placement = Placement(translation, rotation, center)
    result.Label = title
    return result


def boolean(type, base, tool):
    result = doc.addObject(type)
    result.Base = base
    result.Tool = tool
    result.Refine = True
    base.Visibility = False
    tool.Visibility = False
    return result


def fuse(*objects):
    if len(objects) == 1:
        return objects[0]
    if len(objects) == 2:
        return boolean(
            "Part::Fuse",
            objects[0],
            objects[1],
        )
    else:
        return fuse(*[fuse(*objects[:2]), *objects[2:]])


def cut(*objects):
    if len(objects) == 1:
        return objects[0]
    if len(objects) == 2:
        return boolean(
            "Part::Cut",
            objects[0],
            objects[1],
        )
    else:
        return cut(*[cut(*objects[:2]), *objects[2:]])


def servo_horn_screw_holes():
    screw_holes = []
    for i in range(8):
        screw_holes.append(
            cylinder(
                diameter=2.2,
                height=1,
                translation=Vector(8, 0, 0),
                rotation=Rotation(Vector(0, 0, 1), i * 360 / 8),
                center=Vector(-8, 0, 0),
            ),
        )
        screw_holes.append(
            cylinder(
                diameter=4,
                height=2,
                translation=Vector(8, 0, 1),
                rotation=Rotation(Vector(0, 0, 1), i * 360 / 8),
                center=Vector(-8, 0, 0),
            ),
        )
    return screw_holes


def servo_horn_center_holes(height):
    cone = doc.addObject("Part::Cone")
    cone.Radius1 = 8.3 / 2
    cone.Radius2 = 8.3 / 2 - 2
    cone.Height = 2
    cone.Placement = Placement(Vector(0, 0, 2.3), Rotation(0, 0, 0))

    return [
        cylinder(
            diameter=6,
            height=3 + height + 1,
        ),
        cylinder(
            diameter=8.3,
            height=2.3,
        ),
        cone
    ]


def winch():
    cone_bottom = doc.addObject("Part::Cone")
    cone_bottom.Radius1 = 12 / 2
    cone_bottom.Radius2 = 10 / 2
    cone_bottom.Height = 1
    cone_bottom.Placement = Placement(Vector(0, 0, 3), Rotation(0, 0, 0))

    cone_top = doc.addObject("Part::Cone")
    cone_top.Radius1 = 10 / 2
    cone_top.Radius2 = 12 / 2
    cone_top.Height = 1
    cone_top.Placement = Placement(Vector(0, 0, 3 + PULLEY_HEIGHT - 1), Rotation(0, 0, 0))

    result = cut(
        fuse(
            cylinder(
                diameter=19.5,
                height=3
            ),
            cylinder(
                diameter=10,
                height=PULLEY_HEIGHT,
                translation=Vector(0, 0, 3)
            ),
            cone_bottom,
            cone_top
        ),
        *servo_horn_center_holes(PULLEY_HEIGHT),
        *servo_horn_screw_holes(),
        cylinder(
            diameter=2,
            height=10,
            translation=Vector(0, 0, 3 + PULLEY_HEIGHT / 2),
            rotation=Rotation(Vector(0, 1, 0), 90)
        )
    )
    result.Label = "winch"
    return result


def makeServoToJointBracket():
    result = doc.addObject("Part::Feature")
    front = Part.makeBox(BRACKET_THICKNESS, MOTOR_WIDTH + BRACKET_THICKNESS, 10).translate(
        Vector(-MOTOR_LENGTH / 2 - BRACKET_THICKNESS, -MOTOR_WIDTH + 11.25, 0)
    )
    side = Part.makeBox(30 * 8, BRACKET_THICKNESS, 10).translate(
        Vector(-MOTOR_LENGTH / 2, 11.25, 0)
    )
    result.Shape = front.fuse(side)
    result.Label = "Servo to Joint Bracket"
    return result


dynamixel = Part.read("XM430-W350-T.stp")
first_winch = winch()
first_winch.Label = "Winch 1"
first_winch.Placement = Placement(Vector(0, 0, 19), Rotation(0, 0, 0))
for i in range(8):
    object = doc.addObject("Part::Feature")
    object.Label = f"Dynamixel {i + 1}"
    object.Shape = dynamixel
    object.Placement = Placement(Vector(i * 30, 0, ), Rotation(0, 0, 0))
    if i != 0:
        object = doc.addObject("App::Link")
        object.Label = f"Winch {i + 1}"
        object.LinkedObject = first_winch
        object.Placement = Placement(Vector(i * 30, 0, 19), Rotation(0, 0, 0))
makeServoToJointBracket()

doc.recompute()
FreeCADGui.ActiveDocument.ActiveView.fitAll()

end_time = time()
print(f"Loaded in {end_time - start_time}s")
