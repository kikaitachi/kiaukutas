from dataclasses import dataclass, field
from FreeCAD import DocumentObject, newDocument, Placement, Rotation, Vector
from PySide2 import QtCore
from math import acos, cos, degrees, pi, radians, sin, sqrt
# from freecad.gears.commands import CreateInvoluteGear
from typing import Optional
import xml.etree.ElementTree as ET
import FreeCADGui
import Part
import sys


@dataclass
class RobotPart:
    """Robot part."""

    object: DocumentObject
    """FreeCAD object."""

    placement: Placement
    """Relative placement."""


@dataclass
class Segment:
    """Segment of the robot arm."""

    placement: Placement
    """Relative placement of the next segment."""

    parts: list[RobotPart] = field(default_factory=list)
    """Parts of the segment."""


SEGMENTS = [
    Segment(
        Placement(
            Vector(-110, 0, 110),
            Rotation(Vector(0, -1, 0), -90),
        )
    ),
    Segment(
        Placement(
            Vector(-110, 0, 0),
            Rotation(Vector(0, 1, 0), 0),
        )
    ),
    Segment(
        Placement(
            Vector(-110, 0, 0),
            Rotation(Vector(0, 1, 0), 0),
        )
    ),
    Segment(
        Placement(
            Vector(-110, 0, 110),
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
PULLEY_HOLE_RADIUS = 7.4 / 2
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
        self.servo_angles = [0, 0, 0, 0, 0, 0, 0, 0]
        self.speed = 0.1

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
        joint_shaft = make_joint_shaft()
        angle = -45
        for i in range(len(SEGMENTS)):
            segment = SEGMENTS[i]

            def make_part(
                        shape,
                        relative_placement: Placement = Placement(
                            Vector(0, 0, 0),
                            Rotation(0, 0, 0),
                        )
                    ) -> DocumentObject:
                global doc
                nonlocal placement, segment
                object = doc.addObject("Part::Feature")
                object.Shape = shape
                object.Placement = placement.multiply(relative_placement)
                segment.parts.append(RobotPart(object, relative_placement))
                return object

            object = make_part(joint_shaft)
            object.Label = f"Joint shaft {i}a"
            object.ViewObject.ShapeColor = JOINT_SHAFT_COLOR

            for j in range(pulley_count):
                object = make_part(
                    pulley,
                    Placement(
                        Vector(0, 0, pulley_start + j * JOINT_PULLEY_SPACING),
                        Rotation(0, 0, 0),
                    )
                )
                object.Label = f"Pulley {i}a{j}"

            placement = placement.multiply(
                Placement(
                    Vector(0, 0, 0),
                    Rotation(angle / 2, 0, 0),
                )
            )
            placement = placement.multiply(
                Placement(
                    Vector(SEGMENT_THICKNESS, 0, 0),
                    Rotation(0, 0, 0),
                )
            )
            placement = placement.multiply(
                Placement(
                    Vector(0, 0, 0),
                    Rotation(angle / 2, 0, 0),
                )
            )

            object = make_part(joint_shaft)
            object.Label = f"Joint shaft {i}b"
            object.ViewObject.ShapeColor = JOINT_SHAFT_COLOR

            for j in range(pulley_count):
                object = make_part(
                    pulley,
                    Placement(
                        Vector(0, 0, pulley_start + j * JOINT_PULLEY_SPACING),
                        Rotation(0, 0, 0),
                    )
                )
                object.Label = f"Pulley {i}b{j}"

            placement = placement.multiply(segment.placement)

            pulley_count -= 1


dir = sys.argv[3]


def add_visual(
        link: ET.Element,
        stl: str,
        xyz: str = "0 0 0",
        rpy: str = "0 0 0",
        rgba: str = "1 1 1 1",
        placement: Optional[Placement] = None
):
    if placement is not None:
        xyz = " ".join(str(x) for x in placement.Base)
        rpy = " ".join(str(radians(x)) for x in placement.Rotation.toEuler())
    visual = ET.SubElement(link, "visual")
    ET.SubElement(visual, "origin", {"xyz": xyz, "rpy": rpy})
    geometry = ET.SubElement(visual, "geometry")
    ET.SubElement(geometry, "mesh", {"filename": f"{stl}.stl"})
    material = ET.SubElement(visual, "material", {"name": ""})
    ET.SubElement(material, "color", {"rgba": rgba})


Part.read("XM430-W350-T.stp").exportStl(f"{dir}/XM430-W350-T.stl")
pulley = make_pulley()
pulley.exportStl(f"{dir}/shaft-pulley.stl")
pulley.exportStep(f"{dir}/shaft-pulley.stp")
shaft = make_joint_shaft()
shaft.exportStl(f"{dir}/shaft.stl")
shaft.exportStep(f"{dir}/shaft.stp")

root = ET.Element("robot", {"name": "kiaukutas"})
base = ET.SubElement(root, "link", {"name": "base"})

for i in range(NUMBER_OF_MOTORS):
    add_visual(base, "XM430-W350-T", f"{i * 30 + 30} 0 0", f"{pi / 2} {pi} 0", "0.05 0.05 0.05 1")

placement = Placement(Vector(0, 0, 10), Rotation(0, 0, 0))
add_visual(base, "shaft", placement=placement)
for i in range(len(SEGMENTS)):
    segment = SEGMENTS[i]
    placement = placement.multiply(
        Placement(
            Vector(-SEGMENT_THICKNESS, 0, 0),
            Rotation(0, 0, 0),
        )
    )
    link = ET.SubElement(root, "link", {"name": f"segment{i * 2}"})
    add_visual(link, "shaft", placement=placement)
    placement = placement.multiply(segment.placement)
    link = ET.SubElement(root, "link", {"name": f"segment{i * 2 + 1}"})
    if i != len(SEGMENTS) - 1:
        add_visual(link, "shaft", placement=placement)
    # visual = ET.SubElement(link, "visual")
    # origin = ET.SubElement(visual, "origin", {"xyz": f"0 0 {i * 5}", "rpy": "0 0 0"})
    # geometry = ET.SubElement(visual, "geometry")
    # mesh = ET.SubElement(geometry, "mesh", {"filename": "shaft-pulley.stl"})
for i in range(12):
    joint = ET.SubElement(root, "joint", {"name": f"joint{i}", type: "revolute"})
    ET.SubElement(joint, "parent", {"link": "base" if i == 0 else f"segment{i - 1}"})
    ET.SubElement(joint, "child", {"link": f"segment{i}"})

tree = ET.ElementTree(root)
tree.write(f"{dir}/robot.urdf")

exit(0)
