from dataclasses import dataclass
from FreeCAD import newDocument, Placement, Rotation, Vector
from math import asin, cos, degrees, pi, radians, sin, sqrt
from freecad.gears.commands import CreateInvoluteGear
from typing import Optional
import xml.etree.ElementTree as ET
import Part
import sys


@dataclass
class Segment:
    """Segment of the robot arm."""

    placement: Placement
    """Relative placement of the next segment."""

    axis: Vector
    """Axis of rotation."""


TOLERANCE = 0.2
JOINT_SHAFT_LENGTH = 100
SHAFT_TO_PLATE = 10
PLATE_THICKNESS = 6
TACKLE_PULLEY_RADIUS = 5 / 2

SEGMENTS = [
    Segment(
        Placement(
            Vector(0, 0, 0),
            Rotation(0, 0, 0),
        ),
        "0 0 1",
    ),
    Segment(
        Placement(
            Vector(-(JOINT_SHAFT_LENGTH + SHAFT_TO_PLATE), 0, JOINT_SHAFT_LENGTH + SHAFT_TO_PLATE),
            Rotation(Vector(0, -1, 0), -90),
        ),
        "0 0 1",
    ),
    Segment(
        Placement(
            Vector(-(JOINT_SHAFT_LENGTH + 2 * SHAFT_TO_PLATE), 0, 0),
            Rotation(Vector(0, 1, 0), 0),
        ),
        "0 0 1",
    ),
    Segment(
        Placement(
            Vector(-(JOINT_SHAFT_LENGTH + 2 * SHAFT_TO_PLATE), 0, 0),
            Rotation(Vector(0, 1, 0), 0),
        ),
        "0 0 1",
    ),
    Segment(
        Placement(
            Vector(-(JOINT_SHAFT_LENGTH + SHAFT_TO_PLATE), 0, JOINT_SHAFT_LENGTH + SHAFT_TO_PLATE),
            Rotation(Vector(0, 1, 0), 90),
        ),
        "0 0 1",
    ),
    Segment(
        Placement(
            Vector(-SHAFT_TO_PLATE, 0, -SHAFT_TO_PLATE),
            Rotation(Vector(0, 1, 0), -90),
        ),
        "0 0 1",
    ),
]

EXTRA_PULLEYS_PER_JOINT = 3
NUMBER_OF_MOTORS = 8
TENDON_RADIUS = 1 / 2

PULLEY_RADIUS = 10 / 2
PULLEY_HEIGHT = 4
PULLEY_HOLE_RADIUS = 7.4 / 2
JOINT_PULLEY_SPACING = 6

BRACKET_THICKNESS = 4
MOTOR_LENGTH = 28.5
MOTOR_WIDTH = 46.5
MOTOR_SPACING = 30

SEGMENT_THICKNESS = 20

JOINT_SHAFT_OD = 5
JOINT_SHAFT_ID = 4
JOINT_SHAFT_COLOR = (0.5, 0.0, 0.0, 0.0)
JOINT_SHAFT_PULLEY_AREA_LENGTH = 70

JOINT_GEAR_TEETH = 11
JOINT_GEAR_HEIGHT = (JOINT_SHAFT_LENGTH - 14 * JOINT_PULLEY_SPACING) / 2

doc = newDocument("kiaukutas")


def make_pulley(
        height: float = PULLEY_HEIGHT,
        pulley_radius: float = PULLEY_RADIUS,
        flange_radius: float = PULLEY_RADIUS + 1,
        hole_radius: float = PULLEY_HOLE_RADIUS,
):
    return Part.makeCylinder(
        pulley_radius, height, Vector(0, 0, 0), Vector(0, 0, 1)
    ).fuse(
        Part.makeCone(
            flange_radius, pulley_radius, 1, Vector(0, 0, 0), Vector(0, 0, 1)
        )
    ).fuse(
        Part.makeCone(
            pulley_radius, flange_radius, 1, Vector(0, 0, height - 1), Vector(0, 0, 1)
        )
    ).cut(
        Part.makeCylinder(
            hole_radius, height, Vector(0, 0, 0), Vector(0, 0, 1)
        )
    ).removeSplitter()


def make_tackle_pulley():
    return Part.makeCylinder(
        TACKLE_PULLEY_RADIUS, 2.1, Vector(0, 0, 0), Vector(0, 1, 0)
    ).fuse(
        Part.makeCylinder(
            7 / 2, 0.6, Vector(0, 0, 0), Vector(0, 1, 0)
        )
    ).cut(
        Part.makeCylinder(
            3 / 2, 2.1, Vector(0, 0, 0), Vector(0, 1, 0)
        )
    ).removeSplitter()


def make_tackle_pulley_tendon():
    return Part.makeTorus(
        TACKLE_PULLEY_RADIUS + TENDON_RADIUS,
        TENDON_RADIUS,
        Vector(0, 0, 0),
        Vector(0, 1, 0),
        0,
        360,
        180,
    )


def make_joint_shaft():
    return Part.makeCylinder(
        JOINT_SHAFT_OD / 2, JOINT_SHAFT_LENGTH, Vector(0, 0, 0), Vector(0, 0, 1)
    ).cut(Part.makeCylinder(
        JOINT_SHAFT_ID / 2, JOINT_SHAFT_LENGTH, Vector(0, 0, 0), Vector(0, 0, 1)
    )).removeSplitter()


def make_segment_plate():
    corner_length = SEGMENT_THICKNESS - PLATE_THICKNESS
    joiner_length = sqrt(JOINT_GEAR_HEIGHT ** 2 * 2)
    joiner_center = sqrt(joiner_length ** 2 * 2) / 2
    return Part.makeBox(
        JOINT_SHAFT_LENGTH,
        PLATE_THICKNESS,
        JOINT_SHAFT_LENGTH,
        Vector(0, -PLATE_THICKNESS / 2, 0),
        Vector(0, 0, 1),
    ).fuse(
        Part.makeBox(
            corner_length,
            PLATE_THICKNESS,
            corner_length,
            Vector(JOINT_SHAFT_LENGTH, -PLATE_THICKNESS / 2, JOINT_SHAFT_LENGTH),
            Vector(0, 0, 1),
        )
    ).fuse(
        Part.makeBox(
            joiner_length,
            PLATE_THICKNESS,
            joiner_length,
            Vector(JOINT_SHAFT_LENGTH - joiner_center, -PLATE_THICKNESS / 2, JOINT_SHAFT_LENGTH),
            Vector(1, 0, 1),
        )
    ).fuse(
        Part.makeBox(
            corner_length,
            PLATE_THICKNESS,
            corner_length,
            Vector(-corner_length, -PLATE_THICKNESS / 2, JOINT_SHAFT_LENGTH),
            Vector(0, 0, 1),
        )
    ).fuse(
        Part.makeBox(
            joiner_length,
            PLATE_THICKNESS,
            joiner_length,
            Vector(joiner_center, -PLATE_THICKNESS / 2, JOINT_SHAFT_LENGTH),
            Vector(-1, 0, -1),
        )
    ).fuse(
        Part.makeBox(
            corner_length,
            PLATE_THICKNESS,
            corner_length,
            Vector(JOINT_SHAFT_LENGTH, -PLATE_THICKNESS / 2, -corner_length),
            Vector(0, 0, 1),
        )
    ).fuse(
        Part.makeBox(
            joiner_length,
            PLATE_THICKNESS,
            joiner_length,
            Vector(JOINT_SHAFT_LENGTH + joiner_center, -PLATE_THICKNESS / 2, 0),
            Vector(-1, 0, -1),
        )
    ).fuse(
        Part.makeBox(
            corner_length,
            PLATE_THICKNESS,
            corner_length,
            Vector(-corner_length, -PLATE_THICKNESS / 2, -corner_length),
            Vector(0, 0, 1),
        )
    ).fuse(
        Part.makeBox(
            joiner_length,
            PLATE_THICKNESS,
            joiner_length,
            Vector(joiner_center, -PLATE_THICKNESS / 2, 0),
            Vector(-1, 0, -1),
        )
    # ).cut(
    #     Part.makeCylinder(
    #         3.4 / 2, 3, Vector(JOINT_GEAR_HEIGHT / 2, 0, JOINT_GEAR_HEIGHT / 2), Vector(0, 1, 0)
    #     )
    # ).cut(
    #     Part.makeCylinder(
    #         3.4 / 2, 3, Vector(JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT / 2, 0, JOINT_GEAR_HEIGHT / 2), Vector(0, 1, 0)
    #     )
    # ).cut(
    #     Part.makeCylinder(
    #         3.4 / 2, 3, Vector(JOINT_GEAR_HEIGHT / 2, 0, JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT / 2), Vector(0, 1, 0)
    #     )
    # ).cut(
    #     Part.makeCylinder(
    #         3.4 / 2, 3, Vector(JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT / 2, 0, JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT / 2), Vector(0, 1, 0)
    #     )
    ).removeSplitter()


def makeTendonOnPulley():
    helix = Part.makeHelix(TENDON_RADIUS * 2, TENDON_RADIUS * 4, PULLEY_RADIUS)
    circle = Part.makeCircle(TENDON_RADIUS, Vector(PULLEY_RADIUS, 0, 0), Vector(0, 1, 0))
    return Part.Wire(helix).makePipe(Part.Wire([circle]))


def make_joint_gear(beta):
    gear = CreateInvoluteGear.create()
    gear.teeth = JOINT_GEAR_TEETH
    gear.beta = beta
    gear.double_helix = True
    gear.module = SEGMENT_THICKNESS / gear.teeth
    gear.height = JOINT_GEAR_HEIGHT
    direction = beta / abs(beta)
    connector_thickness = 3
    result = gear.Proxy.generate_gear_shape(gear)

    if beta < 0:
        polygon = Part.makePolygon([
            Vector(-SEGMENT_THICKNESS / 2, 0, 0),
            Vector(SEGMENT_THICKNESS / 2 - PLATE_THICKNESS, 0, SEGMENT_THICKNESS - PLATE_THICKNESS),
            Vector(SEGMENT_THICKNESS / 2 - PLATE_THICKNESS, 0, 0),
            Vector(-SEGMENT_THICKNESS / 2, 0, 0),
        ])
    else:
        polygon = Part.makePolygon([
            Vector(SEGMENT_THICKNESS / 2, 0, 0),
            Vector(-SEGMENT_THICKNESS / 2 + PLATE_THICKNESS, 0, SEGMENT_THICKNESS - PLATE_THICKNESS),
            Vector(-SEGMENT_THICKNESS / 2 + PLATE_THICKNESS, 0, 0),
            Vector(SEGMENT_THICKNESS / 2, 0, 0),
        ])
    face = Part.Face(polygon)
    solid_right = face.extrude(Vector(0, connector_thickness, 0)).translate(
        Vector(0, PLATE_THICKNESS / 2, JOINT_GEAR_HEIGHT)
    )
    solid_left = face.extrude(Vector(0, connector_thickness, 0)).translate(
        Vector(0, -PLATE_THICKNESS / 2 - connector_thickness, JOINT_GEAR_HEIGHT)
    )

    return result.fuse(
        Part.makeBox(SEGMENT_THICKNESS / 2 - JOINT_SHAFT_OD / 2, PLATE_THICKNESS + 2 * connector_thickness, gear.height).translate(
            Vector(JOINT_SHAFT_OD / 2 if direction > 0 else -SEGMENT_THICKNESS / 2, -PLATE_THICKNESS / 2 - connector_thickness, 0)
        ).rotate(
            Vector(0, 0, 0),
            Vector(0, 0, 1),
            360.0 / (JOINT_GEAR_TEETH * 4) * -direction
        )
    ).rotate(
        Vector(0, 0, 0),
        Vector(0, 0, 1),
        360.0 / (JOINT_GEAR_TEETH * 4) * direction
    ).fuse(
        solid_right
    ).fuse(
        solid_left
    ).cut(  # Bunt gear teeth
        Part.makeBox(SEGMENT_THICKNESS / 2 - JOINT_SHAFT_OD / 2, PLATE_THICKNESS + 2 * connector_thickness, gear.height * 2).translate(
            Vector(JOINT_SHAFT_OD / 2 + (SEGMENT_THICKNESS / 2 - JOINT_SHAFT_OD / 2) if direction > 0 else -SEGMENT_THICKNESS / 2 - (SEGMENT_THICKNESS / 2 - JOINT_SHAFT_OD / 2), -PLATE_THICKNESS / 2 - connector_thickness, -gear.height / 2)
        )
    ).cut(  # Connector hole
        Part.makeCylinder(
            3.4 / 2, SEGMENT_THICKNESS * 2,
            Vector(0, -SEGMENT_THICKNESS, JOINT_GEAR_HEIGHT + SEGMENT_THICKNESS / 2 - PLATE_THICKNESS),
            Vector(0, 1, 0),
        )
    ).cut(  # Shaft hole
        Part.makeCylinder(
            JOINT_SHAFT_OD / 2 + TOLERANCE, JOINT_GEAR_HEIGHT * 2,
            Vector(0, 0, -JOINT_GEAR_HEIGHT / 2),
            Vector(0, 0, 1),
        )
    ).cut(  # Plate cavity
        Part.makeBox(
            PLATE_THICKNESS, PLATE_THICKNESS, PLATE_THICKNESS
        ).translate(
            Vector(-PLATE_THICKNESS / 2, -PLATE_THICKNESS / 2, -PLATE_THICKNESS / 2)
        ).rotate(
            Vector(0, 0, 0),
            Vector(0, 1, 0),
            45,
        ).translate(
            Vector(PLATE_THICKNESS / 2, PLATE_THICKNESS / 2, PLATE_THICKNESS / 2)
        ).translate(
            Vector(SEGMENT_THICKNESS / 2 - PLATE_THICKNESS / 2 if direction > 0 else -SEGMENT_THICKNESS / 2 - PLATE_THICKNESS / 2, -PLATE_THICKNESS / 2, JOINT_GEAR_HEIGHT - PLATE_THICKNESS / 2)
        )
    ).removeSplitter()


def make_winch():
    winch = Part.makeCylinder(
        19.5 / 2, 3, Vector(0, 0, 0), Vector(0, 0, 1)
    ).fuse(
        Part.makeCone(
            12 / 2, 10 / 2, 1, Vector(0, 0, 3), Vector(0, 0, 1)
        )
    ).fuse(
        Part.makeCylinder(
            PULLEY_RADIUS, PULLEY_HEIGHT, Vector(0, 0, 3), Vector(0, 0, 1)
        )
    ).fuse(
        Part.makeCone(
            PULLEY_RADIUS, 12 / 2, 1, Vector(0, 0, 3 + PULLEY_HEIGHT - 1), Vector(0, 0, 1)
        )
    ).cut(
        Part.makeCylinder(
            2 / 2, 10, Vector(0, 0, 3 + PULLEY_HEIGHT / 2), Vector(0, 1, 0)
        )
    )

    for i in range(8):
        winch = winch.cut(
            Part.makeCylinder(
                2.2 / 2, 1, Vector(8 * sin(i * 2 * pi / 8), 8 * cos(i * 2 * pi / 8), 0), Vector(0, 0, 1)
            )
        ).cut(
            Part.makeCylinder(
                4 / 2, 2, Vector(8 * sin(i * 2 * pi / 8), 8 * cos(i * 2 * pi / 8), 1), Vector(0, 0, 1)
            )
        )

    return winch.cut(
        Part.makeCylinder(
            6 / 2, 3 + PULLEY_HEIGHT + 1, Vector(0, 0, 0), Vector(0, 0, 1)
        )
    ).cut(
        Part.makeCylinder(
            8.3 / 2, 2.3, Vector(0, 0, 0), Vector(0, 0, 1)
        )
    ).cut(
        Part.makeCone(
            8.3 / 2, 8.3 / 2 - 2, 2, Vector(0, 0, 2.3), Vector(0, 0, 1)
        )
    ).removeSplitter()


def add_origin(
    element: ET.Element,
    xyz: str = "0 0 0",
    rpy: str = "0 0 0",
    placement: Optional[Placement] = None
) -> ET.Element:
    if placement is not None:
        xyz = " ".join(str(x) for x in placement.Base)
        rpy = " ".join(str(radians(x)) for x in placement.Rotation.toEuler())
    return ET.SubElement(element, "origin", {"xyz": xyz, "rpy": rpy})


def add_visual(
        link: ET.Element,
        stl: str,
        xyz: str = "0 0 0",
        rpy: str = "0 0 0",
        rgba: str = "1 1 1 1",
        placement: Optional[Placement] = None,
        name: Optional[str] = None
):
    visual = ET.SubElement(link, "visual")
    add_origin(visual, xyz, rpy, placement)
    geometry = ET.SubElement(visual, "geometry")
    ET.SubElement(geometry, "mesh", {"filename": f"{stl}.stl"})
    material = ET.SubElement(visual, "material", {"name": "" if name is None else name})
    if name is None:
        ET.SubElement(material, "color", {"rgba": rgba})


def add_tendon(
        link: ET.Element,
        length: float,
        placement: Placement,
        index: int = 0,
):
    visual = ET.SubElement(link, "visual")
    add_origin(
        visual,
        placement=placement.multiply(
            Placement(
                Vector(0, 0, length / 2),
                Rotation(0, 0, 0),
            )
        )
    )
    geometry = ET.SubElement(visual, "geometry")
    ET.SubElement(
        geometry,
        "cylinder",
        {
            "radius": f"{TENDON_RADIUS}",
            "length": f"{length}",
        }
    )
    ET.SubElement(visual, "material", {"name": f"tendon{index}"})


def add_shaft_pulleys(
        link: ET.Element,
        count: int,
        placement: Placement
):
    for i in range(count):
        add_visual(
            link,
            "shaft-pulley",
            placement=placement.multiply(
                Placement(
                    Vector(0, 0, JOINT_SHAFT_LENGTH - i * JOINT_PULLEY_SPACING - 8 - PULLEY_HEIGHT - (JOINT_PULLEY_SPACING - PULLEY_HEIGHT) / 2),
                    Rotation(0, 0, 0),
                )
            )
        )


dir = sys.argv[3]
Part.read("XM430-W350-T.stp").exportStl(f"{dir}/XM430-W350-T.stl")
pulley = make_pulley()
pulley.exportStl(f"{dir}/shaft-pulley.stl")
pulley.exportStep(f"{dir}/shaft-pulley.stp")
tackle_pulley = make_tackle_pulley()
tackle_pulley.exportStl(f"{dir}/tackle-pulley.stl")
tackle_pulley.exportStep(f"{dir}/tackle-pulley.stp")
tackle_pulley_tendon = make_tackle_pulley_tendon()
tackle_pulley_tendon.exportStl(f"{dir}/tackle-pulley-tendon.stl")
tackle_pulley_tendon.exportStep(f"{dir}/tackle-pulley-tendon.stp")
shaft = make_joint_shaft()
shaft.exportStl(f"{dir}/shaft.stl")
shaft.exportStep(f"{dir}/shaft.stp")
segment_plate = make_segment_plate()
segment_plate.exportStl(f"{dir}/segment-plate.stl")
segment_plate.exportStep(f"{dir}/segment-plate.stp")
joint_gear_right = make_joint_gear(30.0)
joint_gear_right.exportStl(f"{dir}/joint-gear-right.stl")
joint_gear_right.exportStep(f"{dir}/joint-gear-right.stp")
joint_gear_left = make_joint_gear(-30.0)
joint_gear_left.exportStl(f"{dir}/joint-gear-left.stl")
joint_gear_left.exportStep(f"{dir}/joint-gear-left.stp")
winch = make_winch()
winch.exportStl(f"{dir}/winch.stl")
winch.exportStep(f"{dir}/winch.stp")

root = ET.Element("robot", {"name": "kiaukutas"})


def define_material(name: str, r: float, g: float, b: float, a: float = 1) -> None:
    global root
    material = ET.SubElement(root, "material", {"name": name})
    ET.SubElement(material, "color", {"rgba": f"{r} {g} {b} {a}"})


define_material("tendon0", 1, 0, 0)  # Red
define_material("tendon1", 1, 165 / 256, 0)  # Orange
define_material("tendon2", 1, 1, 0)  # Yellow
define_material("tendon3", 0, 1, 0)  # Green
define_material("tendon4", 0, 1, 1)  # Cyan
define_material("tendon5", 0, 0, 1)  # Blue
define_material("tendon6", 127 / 256, 0, 1)  # Violet
define_material("tendon7", 192 / 256, 192 / 256, 192 / 256)  # Silver


base = ET.SubElement(root, "link", {"name": "base"})
add_visual(base, "joint-gear-right", placement=Placement(
    Vector(0, 0, 11.25 + JOINT_GEAR_HEIGHT),
    Rotation(180, 0, 0),
), rgba="0 0 1 1")
add_visual(base, "joint-gear-right", placement=Placement(
    Vector(0, 0, 11.25 + JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT),
    Rotation(0, 0, 0),
), rgba="0 0 1 1")

for i in range(NUMBER_OF_MOTORS // 2):
    add_visual(  # Bottom
        base,
        "XM430-W350-T",
        f"{i * 30 + 40} {34 / 2 - 0.5 + PULLEY_HEIGHT / 2} {46.5 - 11.25 + i * JOINT_PULLEY_SPACING}",
        f"{pi / 2} 0 0",
        "0.05 0.05 0.05 1"
    )
    add_visual(  # Top
        base,
        "XM430-W350-T",
        f"{i * 30 + 40} {34 / 2 + 0.5 + PULLEY_HEIGHT / 2 + PULLEY_RADIUS * 2} {46.5 + 11.25 + i * JOINT_PULLEY_SPACING + (JOINT_PULLEY_SPACING * 4 - 2 * 11.25)}",
        f"{pi / 2} {pi} 0",
        "0.05 0.05 0.05 1"
    )
    add_visual(  # Bottom
        base,
        "winch",
        f"{i * 30 + 40} {-PULLEY_RADIUS + PULLEY_HEIGHT / 2 + 3 - TENDON_RADIUS} {46.5 - 11.25 + i * JOINT_PULLEY_SPACING}",
        f"{pi / 2} 0 0"
    )
    add_visual(  # Top
        base,
        "winch",
        f"{i * 30 + 40} {PULLEY_RADIUS + PULLEY_HEIGHT / 2 + 3 + TENDON_RADIUS} {46.5 - 11.25 + (i + 4) * JOINT_PULLEY_SPACING}",
        f"{pi / 2} 0 0"
    )
    add_tendon(  # Bottom
        base,
        i * 30 + 40,
        Placement(
            Vector(
                0,
                -PULLEY_RADIUS - TENDON_RADIUS,
                11.25 + JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (i + 3.5),
            ),
            Rotation(0, 90, 0),
        ),
        i,
    )
    add_tendon(  # Top
        base,
        i * 30 + 40,
        Placement(
            Vector(
                0,
                PULLEY_RADIUS + TENDON_RADIUS,
                11.25 + JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (i + 3.5 + 4),
            ),
            Rotation(0, 90, 0),
        ),
        i + 4,
    )


def add_tension_pulleys(
        link,
        index: int,
        placement=Placement(Vector(0, 0, 0), Rotation(0, 0, 0)),
):
    add_visual(link, "tackle-pulley", placement=placement.multiply(
        Placement(
            Vector(
                SHAFT_TO_PLATE + 7 / 2,
                -PULLEY_RADIUS - TENDON_RADIUS - 2.1 + (2.1 - 0.6) / 2,
                JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * 2,
            ),
            Rotation(0, 0, 0),
        )
    ), rgba="0.3 0.2 0.6 1")
    add_visual(
        link,
        "tackle-pulley-tendon",
        placement=placement.multiply(
            Placement(
                Vector(
                    SHAFT_TO_PLATE + 7 / 2,
                    -PULLEY_RADIUS - TENDON_RADIUS,
                    JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * 2,
                ),
                Rotation(0, 0, 0),
            )
        ),
        name=f"tendon{index}"
    )
    for k in range(3):
        add_tendon(
            link,
            7 / 2 + SHAFT_TO_PLATE,
            placement.multiply(
                Placement(
                    Vector(
                        SHAFT_TO_PLATE + 7 / 2,
                        -PULLEY_RADIUS - TENDON_RADIUS,
                        JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (0.5 + k),
                    ),
                    Rotation(0, -90, 0),
                )
            ),
            index,
        )


add_tension_pulleys(
    base,
    0,
    placement=Placement(Vector(0, 0, 11.25), Rotation(0, 0, 0))
)

initial_placement = Placement(Vector(0, 0, 11.25), Rotation(0, 0, 0))
placement = Placement(Vector(0, 0, 0), Rotation(0, 0, 0))
prev_link = base
for i in range(len(SEGMENTS)):
    segment = SEGMENTS[i]

    link = ET.SubElement(root, "link", {"name": f"segment{i}a"})
    add_visual(link, "shaft", placement=placement, rgba="0 1 0 1")
    add_shaft_pulleys(link, 14 - i, placement)

    # Bottom tendons between joint pulleys
    for j in range(4):
        add_tendon(
            link,
            SEGMENT_THICKNESS,
            Placement(
                Vector(
                    0,
                    -PULLEY_RADIUS - TENDON_RADIUS,
                    JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (i + j + 0.5),
                ),
                Rotation(0, -90, 0),
            ),
            i,
        )
    # Crossed tendons between joint pulleys
    for j in range(i + 1, len(SEGMENTS) + 1):
        angle_radians = asin((PULLEY_RADIUS + TENDON_RADIUS) / (SEGMENT_THICKNESS / 2))
        angle_degrees = degrees(angle_radians)
        offset_x = sin(angle_radians) * (PULLEY_RADIUS + TENDON_RADIUS)
        offset_y = cos(angle_radians) * (PULLEY_RADIUS + TENDON_RADIUS)
        add_tendon(
            link,
            2 * sqrt((SEGMENT_THICKNESS / 2) ** 2 - (PULLEY_RADIUS + TENDON_RADIUS) ** 2),
            Placement(
                Vector(
                    -offset_x,
                    -offset_y if j <= len(SEGMENTS) // 2 else offset_y,
                    JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (i + j + 3.5),
                ),
                Rotation(0, -90, -angle_degrees if j <= len(SEGMENTS) // 2 else angle_degrees),
            ),
            j,
        )

    link = ET.SubElement(root, "link", {"name": f"segment{i}b"})
    add_visual(link, "shaft", placement=placement, rgba="1 0 0 1")
    add_shaft_pulleys(link, 14 - i, placement)
    add_visual(link, "joint-gear-left", placement=Placement(
        Vector(0, 0, JOINT_GEAR_HEIGHT),
        Rotation(180, 0, 0),
    ), rgba="0 1 1 1")
    add_visual(link, "joint-gear-left", placement=Placement(
        Vector(0, 0, JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT),
        Rotation(0, 0, 0),
    ), rgba="0 1 1 1")
    add_visual(
        link,
        "segment-plate",
        placement=placement.multiply(
            Placement(
                Vector(-JOINT_SHAFT_LENGTH - SHAFT_TO_PLATE, 0, 0),
                Rotation(0, 0, 0),
            )
        ),
        rgba="1 1 1 0.5",
    )

    # Direction changing pulleys
    if i in (0, 3, 4):
        for j in range(i + 4, 10 - i):
            add_visual(link, "tackle-pulley", placement=Placement(
                Vector(
                    -JOINT_SHAFT_LENGTH + JOINT_GEAR_HEIGHT + j * JOINT_PULLEY_SPACING,
                    -PULLEY_RADIUS - TENDON_RADIUS - 2.1 + (2.1 - 0.6) / 2,
                    JOINT_GEAR_HEIGHT + (j + 1) * JOINT_PULLEY_SPACING,
                ),
                Rotation(0, 0, 0),
            ), rgba="0.3 0.2 0.6 1")
            add_tendon(
                link,
                JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT - j * JOINT_PULLEY_SPACING,
                Placement(
                    Vector(
                        0,
                        PULLEY_RADIUS + TENDON_RADIUS if j < 14 // 2 else -PULLEY_RADIUS - TENDON_RADIUS,
                        JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (j + 1 + i) - JOINT_PULLEY_SPACING / 2,
                    ),
                    Rotation(0, -90, 0),
                ),
                i if j < i + 3 else j - 3,
            )

    for j in range(0, 3, 2):
        add_visual(link, "tackle-pulley", placement=Placement(
            Vector(
                -SHAFT_TO_PLATE - 7 / 2,
                -PULLEY_RADIUS - TENDON_RADIUS - 2.1 + (2.1 - 0.6) / 2,
                JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (2 - j + 1 + i),
            ),
            Rotation(0, 0, 0),
        ), rgba="0.3 0.2 0.6 1")
        for k in [-JOINT_PULLEY_SPACING / 2, JOINT_PULLEY_SPACING / 2]:
            add_tendon(
                link,
                7 / 2 + SHAFT_TO_PLATE,
                Placement(
                    Vector(
                        -SHAFT_TO_PLATE - 7 / 2,
                        -PULLEY_RADIUS - TENDON_RADIUS,
                        JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (2 - j + 1 + i) + k,
                    ),
                    Rotation(0, 90, 0),
                ),
                i,
            )
        add_visual(
            link,
            "tackle-pulley-tendon",
            placement=Placement(
                Vector(
                    -SHAFT_TO_PLATE - 7 / 2,
                    -PULLEY_RADIUS - TENDON_RADIUS,
                    JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (2 - j + 1 + i),
                ),
                Rotation(0, 180, 0),
            ),
            name=f"tendon{i}"
        )

    if i != len(SEGMENTS) - 1:
        add_visual(link, "joint-gear-right", placement=SEGMENTS[i + 1].placement.multiply(
            Placement(
                Vector(0, 0, JOINT_GEAR_HEIGHT),
                Rotation(180, 0, 0),
            ) if SEGMENTS[i + 1].placement.Rotation.Angle == 0 else Placement(
                Vector(0, 0, JOINT_GEAR_HEIGHT),
                Rotation(180, 180, 0),
            )
        ), rgba="1 0 1 1")
        add_visual(link, "joint-gear-right", placement=SEGMENTS[i + 1].placement.multiply(
            Placement(
                Vector(0, 0, JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT),
                Rotation(0, 0, 0),
            )
        ), rgba="1 0 1 1")
        add_tension_pulleys(
            link,
            i + 1,
            placement=SEGMENTS[i + 1].placement.multiply(
                Placement(
                    Vector(
                        0,
                        0,
                        JOINT_PULLEY_SPACING * (i + 1),
                    ),
                    Rotation(0, 0, 0),
                )
            ),
        )

placement = initial_placement
for i in range(len(SEGMENTS)):
    segment = SEGMENTS[i]
    joint = ET.SubElement(root, "joint", {"name": f"joint{i}a", "type": "revolute"})
    ET.SubElement(joint, "parent", {"link": "base" if i == 0 else f"segment{i - 1}b"})
    ET.SubElement(joint, "child", {"link": f"segment{i}a"})
    ET.SubElement(joint, "axis", {"xyz": f"{segment.axis}"})
    ET.SubElement(joint, "limit", {"lower": f"{-pi / 2}", "upper": f"{pi / 2}", "effort": "1", "velocity": "1"})
    add_origin(joint, placement=initial_placement if i == 0 else segment.placement)

    joint = ET.SubElement(root, "joint", {"name": f"joint{i}b", "type": "revolute"})
    ET.SubElement(joint, "parent", {"link": f"segment{i}a"})
    ET.SubElement(joint, "child", {"link": f"segment{i}b"})
    ET.SubElement(joint, "mimic", {"joint": f"joint{i}a"})
    ET.SubElement(joint, "axis", {"xyz": f"{segment.axis}"})
    ET.SubElement(joint, "limit", {"lower": f"{-pi / 2}", "upper": f"{pi / 2}", "effort": "1", "velocity": "1"})
    add_origin(joint, placement=Placement(
        Vector(-SEGMENT_THICKNESS, 0, 0),
        Rotation(0, 0, 0),
    ))

ET.ElementTree(root).write(f"{dir}/robot.urdf")

exit(0)
