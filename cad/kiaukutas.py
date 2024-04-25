from dataclasses import dataclass
from FreeCAD import newDocument, Placement, Rotation, Vector
from PySide2 import QtCore
from freecad.gears.commands import CreateInvoluteGear
from typing import Optional
import FreeCAD
import FreeCADGui
import Part
import math


@dataclass
class Segment:
    placement: Placement


SEGMENTS = [
    Segment(
        Placement(
            Vector(110, 0, 110),
            Rotation(Vector(0, -1, 0), 90),
        )
    ),
    Segment(
        Placement(
            Vector(110, 0, 0),
            Rotation(Vector(0, 1, 0), 0),
        )
    ),
    Segment(
        Placement(
            Vector(110, 0, 0),
            Rotation(Vector(0, 1, 0), 0),
        )
    ),
    Segment(
        Placement(
            Vector(110, 0, 110),
            Rotation(Vector(0, 1, 0), -90),
        )
    ),
    Segment(
        Placement(
            Vector(10, 0, -10),
            Rotation(Vector(0, 1, 0), 90),
        )
    ),
    Segment(
        Placement(
            Vector(0, 0, 0),
            Rotation(0, 0, 0),
        )
    ),
]

EXTRA_PULLEYS_PER_JOINT = 3
NUMBER_OF_MOTORS = 8
TENDON_RADIUS = 1 / 2

PULLEY_RADIUS = 10 / 2
PULLEY_HEIGHT = 4
PULLEY_HOLE_RADIUS = 7.2 / 2
JOINT_PULLEY_SPACING = 5

BRACKET_THICKNESS = 4
MOTOR_LENGTH = 28.5
MOTOR_WIDTH = 46.5
MOTOR_SPACING = 30

SEGMENT_THICKNESS = 16

JOINT_SHAFT_LENGTH = 100
JOINT_SHAFT_OD = 5
JOINT_SHAFT_ID = 4
JOINT_SHAFT_COLOR = (0.5, 0.0, 0.0, 0.0)
JOINT_SHAFT_PULLEY_AREA_LENGTH = 70

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


def make_pulley():
    return Part.makeCylinder(
        PULLEY_RADIUS, PULLEY_HEIGHT, Vector(0, 0, 0), Vector(0, 0, 1)
    ).fuse(Part.makeCone(
        PULLEY_RADIUS + 1, PULLEY_RADIUS, 1, Vector(0, 0, 0), Vector(0, 0, 1)
    )).fuse(Part.makeCone(
        PULLEY_RADIUS, PULLEY_RADIUS + 1, 1, Vector(0, 0, PULLEY_HEIGHT - 1), Vector(0, 0, 1)
    )).cut(Part.makeCylinder(
        PULLEY_HOLE_RADIUS, PULLEY_HEIGHT, Vector(0, 0, 0), Vector(0, 0, 1)
    )).removeSplitter()


def make_joint_shaft():
    return Part.makeCylinder(
        JOINT_SHAFT_OD / 2, JOINT_SHAFT_LENGTH, Vector(0, 0, 0), Vector(0, 0, 1)
    ).cut(Part.makeCylinder(
        JOINT_SHAFT_ID / 2, JOINT_SHAFT_LENGTH, Vector(0, 0, 0), Vector(0, 0, 1)
    )).removeSplitter()


def makeTendonOnPulley():
    helix = Part.makeHelix(TENDON_RADIUS * 2, TENDON_RADIUS * 4, PULLEY_RADIUS)
    circle = Part.makeCircle(TENDON_RADIUS, Vector(PULLEY_RADIUS, 0, 0), Vector(0, 1, 0))
    return Part.Wire(helix).makePipe(Part.Wire([circle]))


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


class Assembly:
    def __init__(self) -> None:
        self.t = 0
        self.make_everything()

        doc.recompute()
        FreeCADGui.ActiveDocument.ActiveView.fitAll()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(lambda: self.animate())
        self.timer.start(10)

    def make_everything(self):
        dynamixel = Part.read("XM430-W350-T.stp")
        first_winch = winch()
        first_winch.Label = "Winch 1"
        first_winch.Placement = Placement(Vector(0, 0, 19), Rotation(0, 0, 0))
        tendonAngle = math.acos(math.sqrt(1 - PULLEY_HEIGHT ** 2 / MOTOR_SPACING ** 2))
        self.winches = [first_winch]
        pulley = make_pulley()
        for i in range(-EXTRA_PULLEYS_PER_JOINT, NUMBER_OF_MOTORS + EXTRA_PULLEYS_PER_JOINT):
            deltaHeight = (PULLEY_RADIUS + TENDON_RADIUS) * 2 if i >= NUMBER_OF_MOTORS // 2 else 0
            tendonLength = MOTOR_SPACING * (i + 1) * math.cos(tendonAngle)
            if i in range(NUMBER_OF_MOTORS):
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
                    self.winches.append(object)

                object = doc.addObject("Part::Feature")
                object.Label = f"Tendon {i + 1}"
                object.ViewObject.ShapeColor = (0.2, 0.6, 0.2, 0.0)
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
            object.Label = f"Pulley 1a.{i + 1}"
            object.Shape = pulley
            object.Placement = Placement(Vector(
                i * 30 + (PULLEY_RADIUS + TENDON_RADIUS) * math.sin(tendonAngle) - tendonLength * math.cos(tendonAngle),
                (PULLEY_RADIUS + TENDON_RADIUS) * math.cos(tendonAngle) + tendonLength * math.sin(tendonAngle),
                19 + 3 + PULLEY_HEIGHT / 2 + (PULLEY_RADIUS + TENDON_RADIUS),
            ), Rotation(0, 90, 90 + math.degrees(tendonAngle)))

            object = doc.addObject("Part::Feature")
            object.Label = f"Pulley 1b.{i + 1}"
            object.Shape = pulley
            object.Placement = Placement(Vector(
                i * 30 + (PULLEY_RADIUS + TENDON_RADIUS) * math.sin(tendonAngle) - (tendonLength + SEGMENT_THICKNESS) * math.cos(tendonAngle),
                (PULLEY_RADIUS + TENDON_RADIUS) * math.cos(tendonAngle) + (tendonLength + SEGMENT_THICKNESS) * math.sin(tendonAngle),
                19 + 3 + PULLEY_HEIGHT / 2 + (PULLEY_RADIUS + TENDON_RADIUS),
            ), Rotation(0, 90, 90 + math.degrees(tendonAngle)))

            if i <= 0:
                delta_x = math.sin(tendonAngle) * PULLEY_HEIGHT / 2
                delta_y = math.cos(tendonAngle) * PULLEY_HEIGHT / 2
                if abs(i) % 2 == 0:
                    object = doc.addObject("Part::Feature")
                    object.Label = f"Pulley 1b.{i + 1}"
                    object.Shape = pulley
                    object.Placement = Placement(Vector(
                        -delta_x + i * 30 + (PULLEY_RADIUS + TENDON_RADIUS) * math.sin(tendonAngle) - (tendonLength + SEGMENT_THICKNESS + PULLEY_RADIUS * 3) * math.cos(tendonAngle),
                        -delta_y + (PULLEY_RADIUS + TENDON_RADIUS) * math.cos(tendonAngle) + (tendonLength + SEGMENT_THICKNESS + PULLEY_RADIUS * 3) * math.sin(tendonAngle),
                        19 + 3 + PULLEY_HEIGHT / 2 + (PULLEY_RADIUS + TENDON_RADIUS),
                    ), Rotation(0, 90, 90 + math.degrees(tendonAngle)))
                elif i != -EXTRA_PULLEYS_PER_JOINT:
                    object = doc.addObject("Part::Feature")
                    object.Label = f"Pulley 1b.{i + 1}"
                    object.Shape = pulley
                    object.Placement = Placement(Vector(
                        -delta_x + i * 30 + (PULLEY_RADIUS + TENDON_RADIUS) * math.sin(tendonAngle) - (tendonLength - PULLEY_RADIUS * 3) * math.cos(tendonAngle),
                        -delta_y + (PULLEY_RADIUS + TENDON_RADIUS) * math.cos(tendonAngle) + (tendonLength - PULLEY_RADIUS * 3) * math.sin(tendonAngle),
                        19 + 3 + PULLEY_HEIGHT / 2 + (PULLEY_RADIUS + TENDON_RADIUS),
                    ), Rotation(0, 90, 90 + math.degrees(tendonAngle)))

        makeServoToJointBracket()

        object = doc.addObject("Part::Feature")
        object.Label = "Tendon on pulley"
        object.Shape = makeTendonOnPulley()
        object.Placement = Placement(Vector(-40, -40, 0), Rotation(0, 0, 0))

        placement = Placement(Vector(-50, -50, 0), Rotation(0, 0, 0))
        pulley_count = len(SEGMENTS) + 2 + 2 * EXTRA_PULLEYS_PER_JOINT
        pulley_start = (
            (JOINT_SHAFT_LENGTH - JOINT_SHAFT_PULLEY_AREA_LENGTH) / 2 +
            (JOINT_PULLEY_SPACING - PULLEY_HEIGHT) / 2
        )
        for i in range(len(SEGMENTS)):
            segment = SEGMENTS[i]

            object = doc.addObject("Part::Feature")
            object.Label = f"Joint shaft {i}a"
            object.Shape = make_joint_shaft()
            object.Placement = placement
            object.ViewObject.ShapeColor = JOINT_SHAFT_COLOR

            for j in range(pulley_count):
                object = doc.addObject("Part::Feature")
                object.Label = f"Pulley {i}a{j}"
                object.Shape = pulley
                object.Placement = placement.multiply(
                    Placement(
                        Vector(0, 0, pulley_start + j * JOINT_PULLEY_SPACING),
                        Rotation(0, 0, 0),
                    )
                )

            placement = placement.multiply(
                Placement(
                    Vector(SEGMENT_THICKNESS, 0, 0),
                    Rotation(0, 0, 0),
                )
            )

            object = doc.addObject("Part::Feature")
            object.Label = f"Joint shaft {i}b"
            object.Shape = make_joint_shaft()
            object.Placement = placement
            object.ViewObject.ShapeColor = JOINT_SHAFT_COLOR

            for j in range(pulley_count):
                object = doc.addObject("Part::Feature")
                object.Label = f"Pulley {i}b{j}"
                object.Shape = pulley
                object.Placement = placement.multiply(
                    Placement(
                        Vector(0, 0, pulley_start + j * JOINT_PULLEY_SPACING),
                        Rotation(0, 0, 0),
                    )
                )

            placement = placement.multiply(segment.placement)
            placement = placement.multiply(
                Placement(
                    Vector(0, 0, 0),
                    Rotation(-45, 0, 0),
                )
            )

            pulley_count -= 1

    def animate(self):
        for winch in self.winches:
            winch.Placement = Placement(winch.Placement.Base, Rotation(1.1 * self.t, 0, 0))
        self.t += 0.1


Assembly()


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
