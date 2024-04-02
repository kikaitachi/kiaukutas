from FreeCAD import newDocument, Placement, Rotation, Vector
from PySide2 import QtCore
from freecad.gears.commands import CreateInvoluteGear
from time import time
from typing import Optional
import FreeCAD
import FreeCADGui
import Part
import math

start_time = time()

NUMBER_OF_MOTORS = 8
TENDON_RADIUS = 1 / 2
PULLEY_RADIUS = 10 / 2
PULLEY_HEIGHT = 4
BRACKET_THICKNESS = 4
MOTOR_LENGTH = 28.5
MOTOR_WIDTH = 46.5
MOTOR_SPACING = 30

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


def makePulley():
    return Part.makeCylinder(
        PULLEY_RADIUS, PULLEY_HEIGHT, Vector(0, 0, -PULLEY_HEIGHT / 2), Vector(0, 0, 1)
    )


def joint_gear(*, translation=Vector(0, 0, 0), rotation=Rotation(0, 0, 0)):
    result = CreateInvoluteGear.create()
    result.teeth = 15
    result.module = 1.9
    result.height = 4
    result.Placement = Placement(translation, rotation)
    return result


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
    bracketHeight = 16
    servoScrewRadius = 3 / 2
    motorChamferLength = 3.5
    motorChamferWidth = 2
    front = Part.makeBox(BRACKET_THICKNESS, MOTOR_WIDTH + BRACKET_THICKNESS - motorChamferWidth, bracketHeight).translate(
        Vector(-MOTOR_LENGTH / 2 - BRACKET_THICKNESS, -MOTOR_WIDTH + 11.25 + motorChamferWidth, -bracketHeight / 2)
    ).cut(Part.makeCylinder(
        servoScrewRadius, BRACKET_THICKNESS, Vector(-MOTOR_LENGTH / 2, -4, 6), Vector(-1, 0, 0))
    ).cut(Part.makeCylinder(
        servoScrewRadius, BRACKET_THICKNESS, Vector(-MOTOR_LENGTH / 2, -4, -6), Vector(-1, 0, 0))
    ).cut(Part.makeCylinder(
        servoScrewRadius, BRACKET_THICKNESS, Vector(-MOTOR_LENGTH / 2, -4 - 24, 6), Vector(-1, 0, 0))
    ).cut(Part.makeCylinder(
        servoScrewRadius, BRACKET_THICKNESS, Vector(-MOTOR_LENGTH / 2, -4 - 24, -6), Vector(-1, 0, 0))
    )
    side = Part.makeBox(MOTOR_SPACING * NUMBER_OF_MOTORS - motorChamferLength, BRACKET_THICKNESS, bracketHeight).translate(
        Vector(-MOTOR_LENGTH / 2, 11.25, -bracketHeight / 2)
    )
    for i in range(NUMBER_OF_MOTORS):
        x = MOTOR_SPACING * i - (MOTOR_LENGTH + motorChamferLength - 16) / 2
        side = side.cut(Part.makeCylinder(
            servoScrewRadius, BRACKET_THICKNESS, Vector(x, 11.25, 6), Vector(0, 1, 0))
        ).cut(Part.makeCylinder(
            servoScrewRadius, BRACKET_THICKNESS, Vector(x + 16, 11.25, 6), Vector(0, 1, 0))
        )
    result.Shape = front.fuse(side)
    result.Label = "Servo to Joint Bracket"
    return result


dynamixel = Part.read("XM430-W350-T.stp")
first_winch = winch()
first_winch.Label = "Winch 1"
first_winch.Placement = Placement(Vector(0, 0, 19), Rotation(0, 0, 0))
tendonAngle = math.acos(math.sqrt(1 - PULLEY_HEIGHT ** 2 / MOTOR_SPACING ** 2))
winches = [first_winch]
pulley = makePulley()
for i in range(NUMBER_OF_MOTORS):
    deltaHeight = (PULLEY_RADIUS + TENDON_RADIUS) * 2 if i >= NUMBER_OF_MOTORS // 2 else 0
    object = doc.addObject("Part::Feature")
    object.Label = f"Dynamixel {i + 1}"
    object.Shape = dynamixel
    object.ViewObject.ShapeColor = (0.3, 0.3, 0.3, 0.0)
    object.Placement = Placement(Vector(i * 30, 0, deltaHeight), Rotation(0, 0, 0))

    if i != 0:
        object = doc.addObject("App::Link")
        object.Label = f"Winch {i + 1}"
        object.LinkedObject = first_winch
        object.Placement = Placement(Vector(i * 30, 0, 19 + deltaHeight), Rotation(0, 0, 0))
        winches.append(object)

    object = doc.addObject("Part::Feature")
    object.Label = f"Tendon {i + 1}"
    object.ViewObject.ShapeColor = (0.2, 0.6, 0.2, 0.0)
    tendonLength = MOTOR_SPACING * (i + 1) * math.cos(tendonAngle)
    object.Shape = Part.makeCylinder(
        TENDON_RADIUS, tendonLength, Vector(
            (PULLEY_RADIUS + TENDON_RADIUS) * math.sin(tendonAngle),
            (PULLEY_RADIUS + TENDON_RADIUS) * math.cos(tendonAngle),
            0
        ), Vector(-1, math.sin(tendonAngle), 0)
    )
    object.Placement = Placement(Vector(
        i * 30, 0, 19 + 3 + PULLEY_HEIGHT / 2 + deltaHeight), Rotation(0, 0, 0))

    object = doc.addObject("Part::Feature")
    object.Label = f"Pulley 1.{i + 1}"
    object.Shape = pulley
    object.Placement = Placement(Vector(
        i * 30 + (PULLEY_RADIUS + TENDON_RADIUS) * math.sin(tendonAngle),
        (PULLEY_RADIUS + TENDON_RADIUS) * math.cos(tendonAngle),
        19 + 3 + PULLEY_HEIGHT / 2 + (PULLEY_RADIUS + TENDON_RADIUS),
    ), Rotation(0, 90, 90 + math.degrees(tendonAngle)))


makeServoToJointBracket()

doc.recompute()
FreeCADGui.ActiveDocument.ActiveView.fitAll()

end_time = time()
# print(f"Loaded in {end_time - start_time}s")


t = 0


def animate():
    global t
    for winch in winches:
        winch.Placement = Placement(winch.Placement.Base, Rotation(1.1 * t, 0, 0))
    t += 0.1


timer = QtCore.QTimer()
timer.timeout.connect(animate)
# timer.start(5)


# Code bellow if for preventing confirmation dialog on close
class MainWindowFilter(QtCore.QObject):
    def eventFilter(self, obj, ev):
        if ev.type() == QtCore.QEvent.Close:
            for i in FreeCAD.listDocuments():
                FreeCAD.closeDocument(i)
        return False


filter = MainWindowFilter()
mw = FreeCADGui.getMainWindow()
mw.installEventFilter(filter)
