from dataclasses import dataclass
from FreeCAD import newDocument, Placement, Rotation, Vector
from math import asin, cos, degrees, pi, radians, sin, sqrt
from freecad.gears.commands import CreateInvoluteGear
from typing import Optional
from shutil import copyfile
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

EXTRA_PULLEYS_PER_JOINT = 3
NUMBER_OF_MOTORS = 8
TENDON_RADIUS = 1 / 2

PULLEY_RADIUS = 10 / 2
PULLEY_HEIGHT = 4
PULLEY_HOLE_RADIUS = 7.4 / 2
JOINT_PULLEY_SPACING = 6

ARM_START_Z = 11.25
VERTICAL_GAP_BETWEEN_MOTORS = JOINT_PULLEY_SPACING * 4 - 2 * ARM_START_Z

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

JETSON_HOLE_DIAMETER = 2.7
JETSON_VERTICAL_DISTANCE_BETWEEN_HOLES = 60.5 - JETSON_HOLE_DIAMETER
JETSON_HORIZONTAL_DISTANCE_BETWEEN_HOLES = 88.7 - JETSON_HOLE_DIAMETER

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


def make_direction_changing_pulley_tendon():
    return Part.makeTorus(
        TACKLE_PULLEY_RADIUS + TENDON_RADIUS,
        TENDON_RADIUS,
        Vector(0, 0, 0),
        Vector(0, 1, 0),
        0,
        360,
        90,
    )


def make_wrap_joint_pulley_tendon():
    return Part.makeTorus(
        PULLEY_RADIUS + TENDON_RADIUS,
        TENDON_RADIUS,
        Vector(0, 0, 0),
        Vector(0, 0, 1),
        0,
        360,
        360,
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
    # ).fuse(
    #     Part.makeBox(
    #         corner_length,
    #         PLATE_THICKNESS,
    #         corner_length,
    #         Vector(JOINT_SHAFT_LENGTH, -PLATE_THICKNESS / 2, JOINT_SHAFT_LENGTH),
    #         Vector(0, 0, 1),
    #     )
    # ).fuse(
    #     Part.makeBox(
    #         joiner_length,
    #         PLATE_THICKNESS,
    #         joiner_length,
    #         Vector(JOINT_SHAFT_LENGTH - joiner_center, -PLATE_THICKNESS / 2, JOINT_SHAFT_LENGTH),
    #         Vector(1, 0, 1),
    #     )
    # ).fuse(
    #     Part.makeBox(
    #         corner_length,
    #         PLATE_THICKNESS,
    #         corner_length,
    #         Vector(-corner_length, -PLATE_THICKNESS / 2, JOINT_SHAFT_LENGTH),
    #         Vector(0, 0, 1),
    #     )
    # ).fuse(
    #     Part.makeBox(
    #         joiner_length,
    #         PLATE_THICKNESS,
    #         joiner_length,
    #         Vector(joiner_center, -PLATE_THICKNESS / 2, JOINT_SHAFT_LENGTH),
    #         Vector(-1, 0, -1),
    #     )
    # ).fuse(
    #     Part.makeBox(
    #         corner_length,
    #         PLATE_THICKNESS,
    #         corner_length,
    #         Vector(JOINT_SHAFT_LENGTH, -PLATE_THICKNESS / 2, -corner_length),
    #         Vector(0, 0, 1),
    #     )
    # ).fuse(
    #     Part.makeBox(
    #         joiner_length,
    #         PLATE_THICKNESS,
    #         joiner_length,
    #         Vector(JOINT_SHAFT_LENGTH + joiner_center, -PLATE_THICKNESS / 2, 0),
    #         Vector(-1, 0, -1),
    #     )
    # ).fuse(
    #     Part.makeBox(
    #         corner_length,
    #         PLATE_THICKNESS,
    #         corner_length,
    #         Vector(-corner_length, -PLATE_THICKNESS / 2, -corner_length),
    #         Vector(0, 0, 1),
    #     )
    # ).fuse(
    #     Part.makeBox(
    #         joiner_length,
    #         PLATE_THICKNESS,
    #         joiner_length,
    #         Vector(joiner_center, -PLATE_THICKNESS / 2, 0),
    #         Vector(-1, 0, -1),
    #     )
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


def make_joint_gear(beta: float):
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
    # ).fuse(
    #     solid_right
    # ).fuse(
    #     solid_left
    ).cut(  # Blunt gear teeth
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
    # ).cut(  # Plate cavity
    #     Part.makeBox(
    #         PLATE_THICKNESS, PLATE_THICKNESS, PLATE_THICKNESS
    #     ).translate(
    #         Vector(-PLATE_THICKNESS / 2, -PLATE_THICKNESS / 2, -PLATE_THICKNESS / 2)
    #     ).rotate(
    #         Vector(0, 0, 0),
    #         Vector(0, 1, 0),
    #         45,
    #     ).translate(
    #         Vector(PLATE_THICKNESS / 2, PLATE_THICKNESS / 2, PLATE_THICKNESS / 2)
    #     ).translate(
    #         Vector(SEGMENT_THICKNESS / 2 - PLATE_THICKNESS / 2 if direction > 0 else -SEGMENT_THICKNESS / 2 - PLATE_THICKNESS / 2, -PLATE_THICKNESS / 2, JOINT_GEAR_HEIGHT - PLATE_THICKNESS / 2)
    #     )
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


def make_arm_to_body_joiner():
    motor_plate_depth = 30
    # motor_plate_height = 46.5 * 2 + VERTICAL_GAP_BETWEEN_MOTORS
    motor_plate_height = ARM_START_Z + JOINT_SHAFT_LENGTH
    depth = PLATE_THICKNESS + motor_plate_depth
    plate_thickness = 3
    motor_plate_y = PLATE_THICKNESS + (SEGMENT_THICKNESS - PLATE_THICKNESS) / 2
    return Part.makeBox(  # Bar for tackle pulleys
        PLATE_THICKNESS, PLATE_THICKNESS, JOINT_SHAFT_LENGTH
    ).fuse(  # Bottom jointer
        Part.makeBox(
            PLATE_THICKNESS, depth, PLATE_THICKNESS
        )
    ).fuse(  # Top joiner
        Part.makeBox(
            PLATE_THICKNESS, depth, PLATE_THICKNESS
        ).translate(
            Vector(0, 0, JOINT_SHAFT_LENGTH - PLATE_THICKNESS)
        )
    ).fuse(  # Motor plate
        Part.makeBox(
            plate_thickness, motor_plate_depth, motor_plate_height
        ).translate(
            Vector(PLATE_THICKNESS - plate_thickness, motor_plate_y, -ARM_START_Z)
        )
    ).cut(  # Hole for bottom tackle pulley
        Part.makeCylinder(
            2.7 / 2, PLATE_THICKNESS, Vector(0, 0, 0), Vector(0, 1, 0)
        ).translate(
            Vector(PLATE_THICKNESS / 2, 0, JOINT_GEAR_HEIGHT + 2 * JOINT_PULLEY_SPACING)
        )
    ).cut(  # Hole for top tackle pulley
        Part.makeCylinder(
            2.7 / 2, PLATE_THICKNESS, Vector(0, 0, 0), Vector(0, 1, 0)
        ).translate(
            Vector(PLATE_THICKNESS / 2, 0, JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT - 2 * JOINT_PULLEY_SPACING)
        )
    ).cut(  # Close bottom hole for bottom servo
        Part.makeCylinder(
            2.7 / 2, PLATE_THICKNESS * 5, Vector(0, 0, 0), Vector(-1, 0, 0)
        ).translate(
            Vector(PLATE_THICKNESS, 15.5, 46.5 - 11.5 - 4 - 24 - 11)
        )
    ).cut(  # Far bottom hole for bottom servo
        Part.makeCylinder(
            2.7 / 2, PLATE_THICKNESS * 5, Vector(0, 0, 0), Vector(-1, 0, 0)
        ).translate(
            Vector(PLATE_THICKNESS, 15.5 + 12, 46.5 - 11.5 - 4 - 24 - 11)
        )
    ).cut(  # Close top hole for bottom servo
        Part.makeCylinder(
            2.7 / 2, PLATE_THICKNESS * 5, Vector(0, 0, 0), Vector(-1, 0, 0)
        ).translate(
            Vector(PLATE_THICKNESS, 15.5, 46.5 - 11.5 - 4 - 24 - 11 + 24)
        )
    ).cut(  # Far top hole for bottom servo
        Part.makeCylinder(
            2.7 / 2, PLATE_THICKNESS * 5, Vector(0, 0, 0), Vector(-1, 0, 0)
        ).translate(
            Vector(PLATE_THICKNESS, 15.5 + 12, 46.5 - 11.5 - 4 - 24 - 11 + 24)
        )
    ).cut(  # Close bottom hole for top servo
        Part.makeCylinder(
            2.7 / 2, PLATE_THICKNESS * 5, Vector(0, 0, 0), Vector(-1, 0, 0)
        ).translate(
            Vector(PLATE_THICKNESS, 15.5 + (PULLEY_RADIUS + TENDON_RADIUS) * 2, 46.5 - 11.5 - 4 - 24 - 11 + VERTICAL_GAP_BETWEEN_MOTORS + 46.5 + 11 - 3)
        )
    ).cut(  # Far bottom hole for top servo
        Part.makeCylinder(
            2.7 / 2, PLATE_THICKNESS * 5, Vector(0, 0, 0), Vector(-1, 0, 0)
        ).translate(
            Vector(PLATE_THICKNESS, 15.5 + 12 + (PULLEY_RADIUS + TENDON_RADIUS) * 2, 46.5 - 11.5 - 4 - 24 - 11 + VERTICAL_GAP_BETWEEN_MOTORS + 46.5 + 11 - 3)
        )
    ).cut(  # Close top hole for top servo
        Part.makeCylinder(
            2.7 / 2, PLATE_THICKNESS * 5, Vector(0, 0, 0), Vector(-1, 0, 0)
        ).translate(
            Vector(PLATE_THICKNESS, 15.5 + (PULLEY_RADIUS + TENDON_RADIUS) * 2, 46.5 - 11.5 - 4 - 24 - 11 + 24 + VERTICAL_GAP_BETWEEN_MOTORS + 46.5 + 11 - 3)
        )
    ).cut(  # Far top hole for top servo
        Part.makeCylinder(
            2.7 / 2, PLATE_THICKNESS * 5, Vector(0, 0, 0), Vector(-1, 0, 0)
        ).translate(
            Vector(PLATE_THICKNESS, 15.5 + 12 + (PULLEY_RADIUS + TENDON_RADIUS) * 2, 46.5 - 11.5 - 4 - 24 - 11 + 24 + VERTICAL_GAP_BETWEEN_MOTORS + 46.5 + 11 - 3)
        )
    ).fuse(
        make_joint_gear(30.0).rotate(
            Vector(0, 0, 0),
            Vector(1, 0, 0),
            180,
        ).translate(
            Vector(-SEGMENT_THICKNESS / 2, PLATE_THICKNESS / 2, JOINT_GEAR_HEIGHT)
        )
    ).fuse(
        make_joint_gear(30.0).translate(
            Vector(-SEGMENT_THICKNESS / 2, PLATE_THICKNESS / 2, JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT)
        )
    ).removeSplitter()
# add_visual(base, "joint-gear-right", placement=Placement(
#     Vector(0, 0, 11.25 + JOINT_GEAR_HEIGHT),
#     Rotation(180, 0, 0),
# ), rgba="0 0 1 1")
# add_visual(base, "joint-gear-right", placement=Placement(
#     Vector(0, 0, 11.25 + JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT),
#     Rotation(0, 0, 0),
# ), rgba="0 0 1 1")


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


dir = sys.argv[3]
copyfile("XM430-W350-T.stl", f"{dir}/XM430-W350-T.stl")
copyfile("jetson.stl", f"{dir}/jetson.stl")
pulley = make_pulley()
pulley.exportStl(f"{dir}/shaft-pulley.stl")
pulley.exportStep(f"{dir}/shaft-pulley.stp")
tackle_pulley = make_tackle_pulley()
tackle_pulley.exportStl(f"{dir}/tackle-pulley.stl")
tackle_pulley.exportStep(f"{dir}/tackle-pulley.stp")
tackle_pulley_tendon = make_tackle_pulley_tendon()
tackle_pulley_tendon.exportStl(f"{dir}/tackle-pulley-tendon.stl")
tackle_pulley_tendon.exportStep(f"{dir}/tackle-pulley-tendon.stp")
direction_changing_pulley_tendon = make_direction_changing_pulley_tendon()
direction_changing_pulley_tendon.exportStl(f"{dir}/direction-changing-pulley-tendon.stl")
direction_changing_pulley_tendon.exportStep(f"{dir}/direction-changing-pulley-tendon.stp")
wrap_joint_pulley_tendon = make_wrap_joint_pulley_tendon()
wrap_joint_pulley_tendon.exportStl(f"{dir}/wrap_joint_pulley_tendon.stl")
wrap_joint_pulley_tendon.exportStep(f"{dir}/wrap_joint_pulley_tendon.stp")
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
arm_to_body_joiner = make_arm_to_body_joiner()
arm_to_body_joiner.exportStl(f"{dir}/arm_to_body_joiner.stl")
arm_to_body_joiner.exportStep(f"{dir}/arm_to_body_joiner.stp")

root = ET.Element("robot", {"name": "kiaukutas"})


def define_material(name: str, r: float, g: float, b: float, a: float = 1) -> None:
    global root
    material = ET.SubElement(root, "material", {"name": name})
    ET.SubElement(material, "color", {"rgba": f"{r} {g} {b} {a}"})


define_material("tendon0", 1, 0, 0)  # Red
define_material("tendon1", 1, 165 / 255, 0)  # Orange
define_material("tendon2", 1, 1, 0)  # Yellow
define_material("tendon3", 0, 1, 0)  # Green
define_material("tendon4", 0, 1, 1)  # Cyan
define_material("tendon5", 0, 0, 1)  # Blue
define_material("tendon6", 127 / 255, 0, 1)  # Violet
define_material("tendon7", 165 / 255, 42 / 255, 42 / 255)  # Brown


base = ET.SubElement(root, "link", {"name": "base"})
# add_visual(base, "joint-gear-right", placement=Placement(
#     Vector(0, 0, 11.25 + JOINT_GEAR_HEIGHT),
#     Rotation(180, 0, 0),
# ), rgba="0 0 1 1")
# add_visual(base, "joint-gear-right", placement=Placement(
#     Vector(0, 0, 11.25 + JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT),
#     Rotation(0, 0, 0),
# ), rgba="0 0 1 1")
add_visual(base, "arm_to_body_joiner", placement=Placement(
    Vector(SEGMENT_THICKNESS / 2, -PLATE_THICKNESS / 2, 11.25),
    Rotation(0, 0, 0),
), rgba="0.5 0.5 0.5 1")

add_visual(
    base,
    "jetson",
    rgba="0.05 0.05 0.05 1",
    placement=Placement(
        Vector(15, 230, 155),
        Rotation(-90, 0, -90),
    )
)

for i in range(NUMBER_OF_MOTORS // 2):
    offset = 28.5 / 2 + SEGMENT_THICKNESS / 2 + PLATE_THICKNESS
    add_visual(  # Bottom
        base,
        "XM430-W350-T",
        f"{i * 30 + offset} {34 / 2 - 0.5 + PULLEY_HEIGHT / 2} {46.5 - 11.25 + i * JOINT_PULLEY_SPACING}",
        f"{pi / 2} 0 0",
        "0.05 0.05 0.05 1"
    )
    add_visual(  # Top
        base,
        "XM430-W350-T",
        f"{i * 30 + offset} {34 / 2 + 0.5 + PULLEY_HEIGHT / 2 + PULLEY_RADIUS * 2} {46.5 + 11.25 + i * JOINT_PULLEY_SPACING + VERTICAL_GAP_BETWEEN_MOTORS}",
        f"{pi / 2} {pi} 0",
        "0.05 0.05 0.05 1"
    )
    add_visual(  # Bottom
        base,
        "winch",
        f"{i * 30 + offset} {-PULLEY_RADIUS + PULLEY_HEIGHT / 2 + 3 - TENDON_RADIUS} {46.5 - 11.25 + i * JOINT_PULLEY_SPACING}",
        f"{pi / 2} 0 0"
    )
    add_visual(  # Top
        base,
        "winch",
        f"{i * 30 + offset} {PULLEY_RADIUS + PULLEY_HEIGHT / 2 + 3 + TENDON_RADIUS} {46.5 - 11.25 + (i + 4) * JOINT_PULLEY_SPACING}",
        f"{pi / 2} 0 0"
    )
    add_tendon(  # Bottom
        base,
        i * 30 + offset,
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
        i * 30 + offset,
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
        direction: int = 1,
):
    add_visual(link, "tackle-pulley", placement=placement.multiply(
        Placement(
            Vector(
                SHAFT_TO_PLATE + PLATE_THICKNESS / 2,
                (-PULLEY_RADIUS - TENDON_RADIUS - 2.1 + (2.1 - 0.6) / 2) * direction,
                JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (2 if direction == 1 else -1),
            ),
            Rotation(0 if direction == 1 else 180, 0, 0),
        )
    ), rgba="0.3 0.2 0.6 1")
    add_visual(
        link,
        "tackle-pulley-tendon",
        placement=placement.multiply(
            Placement(
                Vector(
                    SHAFT_TO_PLATE + 7 / 2,
                    (-PULLEY_RADIUS - TENDON_RADIUS) * direction,
                    JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (2 if direction == 1 else -1),
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
                        (-PULLEY_RADIUS - TENDON_RADIUS) * direction,
                        JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (0.5 + k * direction),
                    ),
                    Rotation(0, -90, 0),
                )
            ),
            index,
        )


def add_non_direction_changing_tendons(tendons: list[Optional[int]]) -> None:
    for i in range(len(tendons)):
        if tendons[i] is not None:
            front_side = tendons[i] > 0
            length = JOINT_SHAFT_LENGTH + SHAFT_TO_PLATE * 2
            add_tendon(
                link,
                length,
                Placement(
                    Vector(
                        -length,
                        PULLEY_RADIUS + TENDON_RADIUS if not front_side else -PULLEY_RADIUS - TENDON_RADIUS,
                        JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (i + 1) - JOINT_PULLEY_SPACING / 2,
                    ),
                    Rotation(0, 90, 0),
                ),
                abs(tendons[i]),
            )


def add_far_tension_pulleys(link, i: int, motor_index: int, direction: bool) -> None:
    for j in range(0, 3, 2):
        add_visual(link, "tackle-pulley", placement=Placement(
            Vector(
                -SHAFT_TO_PLATE - 7 / 2,
                (-PULLEY_RADIUS - TENDON_RADIUS - 2.1 + (2.1 - 0.6) / 2) * direction,
                JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (2 - j * direction + 1 + i),
            ),
            Rotation(0 if direction == 1 else 180, 0, 0),
        ), rgba="0.3 0.2 0.6 1")
        # Far side of block and tackle
        for k in [-JOINT_PULLEY_SPACING / 2, JOINT_PULLEY_SPACING / 2]:
            add_tendon(
                link,
                7 / 2 + SHAFT_TO_PLATE,
                Placement(
                    Vector(
                        -SHAFT_TO_PLATE - 7 / 2,
                        (-PULLEY_RADIUS - TENDON_RADIUS) * direction,
                        JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (2 - j * direction + 1 + i) + k,
                    ),
                    Rotation(0, 90, 0),
                ),
                motor_index,
            )
        add_visual(
            link,
            "tackle-pulley-tendon",
            placement=Placement(
                Vector(
                    -SHAFT_TO_PLATE - 7 / 2,
                    (-PULLEY_RADIUS - TENDON_RADIUS) * direction,
                    JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (2 - j * direction + 1 + i),
                ),
                Rotation(0, 180, 0),
            ),
            name=f"tendon{motor_index}"
        )


def add_joint_tendons(
    prev_link,
    link1,
    link2,
    tendons: list[Optional[tuple[int, str]]],  # motor_index, type
    bottom_pulley1: Optional[Placement] = None,
    top_pulley1: Optional[Placement] = None,
    bottom_pulley2: bool = False,
    top_pulley2: bool = False,
    direction_changing_pulleys: Optional[list[Optional[tuple[int, int, int]]]] = None,
) -> None:
    first_motor_index: Optional[int] = None
    first_tendon_index: Optional[int] = None
    last_motor_index: Optional[int] = None
    last_tendon_index: Optional[int] = None
    for i in range(len(tendons)):
        if tendons[i] is not None:
            motor_index = tendons[i][0]
            if first_motor_index is None:
                first_motor_index = motor_index
                first_tendon_index = i
            last_motor_index = motor_index
            last_tendon_index = i
            tendon_type = tendons[i][1]
            if tendon_type in ["top", "bottom"]:
                add_tendon(
                    link1,
                    SEGMENT_THICKNESS,
                    Placement(
                        Vector(
                            0,
                            (PULLEY_RADIUS + TENDON_RADIUS) * (1 if tendon_type != "top" else -1),
                            JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (i + 0.5),
                        ),
                        Rotation(0, -90, 0),
                    ),
                    motor_index,
                )
            else:
                angle_radians = asin((PULLEY_RADIUS + TENDON_RADIUS) / (SEGMENT_THICKNESS / 2))
                angle_degrees = degrees(angle_radians)
                offset_x = sin(angle_radians) * (PULLEY_RADIUS + TENDON_RADIUS)
                offset_y = cos(angle_radians) * (PULLEY_RADIUS + TENDON_RADIUS)
                add_tendon(
                    link1,
                    2 * sqrt((SEGMENT_THICKNESS / 2) ** 2 - (PULLEY_RADIUS + TENDON_RADIUS) ** 2),
                    Placement(
                        Vector(
                            -offset_x,
                            -offset_y if tendon_type == "falling" else offset_y,
                            JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (i + 0.5),
                        ),
                        Rotation(0, -90, -angle_degrees if tendon_type == "falling" else angle_degrees),
                    ),
                    motor_index,
                )
            add_visual(link1, "wrap_joint_pulley_tendon", placement=Placement(
                Vector(
                    0,
                    0,
                    JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (i + 0.5),
                ),
                Rotation(0, 0, 0),
            ), name=f"tendon{motor_index}")
            add_visual(link2, "wrap_joint_pulley_tendon", placement=Placement(
                Vector(
                    0,
                    0,
                    JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (i + 0.5),
                ),
                Rotation(0, 0, 0),
            ), name=f"tendon{motor_index}")
            add_visual(
                link1,
                "shaft-pulley",
                placement=placement.multiply(
                    Placement(
                        Vector(0, 0, JOINT_GEAR_HEIGHT + i * JOINT_PULLEY_SPACING + (JOINT_PULLEY_SPACING - PULLEY_HEIGHT) / 2),
                        Rotation(0, 0, 0),
                    )
                )
            )
            add_visual(
                link2,
                "shaft-pulley",
                placement=placement.multiply(
                    Placement(
                        Vector(0, 0, JOINT_GEAR_HEIGHT + i * JOINT_PULLEY_SPACING + (JOINT_PULLEY_SPACING - PULLEY_HEIGHT) / 2),
                        Rotation(0, 0, 0),
                    )
                )
            )
    if bottom_pulley1 is not None:
        add_tension_pulleys(
            prev_link,
            first_motor_index,
            bottom_pulley1.multiply(
                Placement(
                    Vector(
                        0,
                        0,
                        JOINT_PULLEY_SPACING * first_tendon_index,
                    ),
                    Rotation(0, 0, 0),
                )
            ),
            1,
        )
    if top_pulley1 is not None:
        add_tension_pulleys(
            prev_link,
            last_motor_index,
            top_pulley1.multiply(
                Placement(
                    Vector(
                        0,
                        0,
                        JOINT_PULLEY_SPACING * last_tendon_index,
                    ),
                    Rotation(0, 0, 0),
                )
            ),
            -1,
        )
    if bottom_pulley2:
        add_far_tension_pulleys(link, first_tendon_index, first_motor_index, 1)
    if top_pulley2:
        add_far_tension_pulleys(link, last_tendon_index - 5, last_motor_index, -1)
    if direction_changing_pulleys is not None:
        for i in range(len(direction_changing_pulleys)):
            if direction_changing_pulleys[i] is not None:
                motor_index = abs(direction_changing_pulleys[i][2])
                front_side = direction_changing_pulleys[i][2] > 0
                src = direction_changing_pulleys[i][0]
                dest = abs(direction_changing_pulleys[i][1])
                inverted = direction_changing_pulleys[i][1] < 0
                horizontal_tendon_length = JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT - dest * JOINT_PULLEY_SPACING + JOINT_PULLEY_SPACING / 2 + TENDON_RADIUS * 2
                vertical_tendon_length = JOINT_SHAFT_LENGTH - JOINT_GEAR_HEIGHT - src * JOINT_PULLEY_SPACING + JOINT_PULLEY_SPACING / 2 + TENDON_RADIUS * 2
                if inverted:
                    vertical_tendon_length = JOINT_SHAFT_LENGTH - vertical_tendon_length + SEGMENT_THICKNESS / 2
                add_visual(link2, "tackle-pulley", placement=Placement(
                    Vector(
                        -horizontal_tendon_length,
                        PULLEY_RADIUS + TENDON_RADIUS + 2.1 - (2.1 - 0.6) / 2 if not front_side else -PULLEY_RADIUS - TENDON_RADIUS - 2.1 + (2.1 - 0.6) / 2,
                        JOINT_GEAR_HEIGHT + (src + 1) * JOINT_PULLEY_SPACING - ((TACKLE_PULLEY_RADIUS + TENDON_RADIUS) * 2 if inverted else 0),
                    ),
                    Rotation(0, 0, 180 if not front_side else 0),
                ), rgba="0.3 0.2 0.6 1")
                add_visual(link2, "direction-changing-pulley-tendon", placement=Placement(
                    Vector(
                        -horizontal_tendon_length,
                        -(PULLEY_RADIUS + TENDON_RADIUS) if front_side else (PULLEY_RADIUS + TENDON_RADIUS),
                        JOINT_GEAR_HEIGHT + (src + 1) * JOINT_PULLEY_SPACING - ((TACKLE_PULLEY_RADIUS + TENDON_RADIUS) * 2 if inverted else 0),
                    ),
                    Rotation(0, 180 + (90 if inverted else 0), 0),
                ), name=f"tendon{motor_index}")
                # Horizontal tendon
                add_tendon(
                    link2,
                    horizontal_tendon_length,
                    Placement(
                        Vector(
                            0,
                            PULLEY_RADIUS + TENDON_RADIUS if not front_side else -PULLEY_RADIUS - TENDON_RADIUS,
                            JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (src + 1) - JOINT_PULLEY_SPACING / 2,
                        ),
                        Rotation(0, -90, 0),
                    ),
                    motor_index,
                )
                # Vertical tendon
                add_tendon(
                    link2,
                    vertical_tendon_length,
                    Placement(
                        Vector(
                            -horizontal_tendon_length - JOINT_PULLEY_SPACING / 2,
                            PULLEY_RADIUS + TENDON_RADIUS if not front_side else -PULLEY_RADIUS - TENDON_RADIUS,
                            JOINT_GEAR_HEIGHT + JOINT_PULLEY_SPACING * (src + 1.5) - JOINT_PULLEY_SPACING / 2 - ((TACKLE_PULLEY_RADIUS + TENDON_RADIUS) * 2 if inverted else 0),
                        ),
                        Rotation(0, 180 if inverted else 0, 0),
                    ),
                    motor_index,
                )


initial_placement = Placement(Vector(0, 0, 11.25), Rotation(0, 0, 0))
placement = Placement(Vector(0, 0, 0), Rotation(0, 0, 0))
prev_link = base
for i in range(len(SEGMENTS)):
    segment = SEGMENTS[i]

    first_link = ET.SubElement(root, "link", {"name": f"segment{i}a"})
    add_visual(first_link, "shaft", placement=placement, rgba="0 1 0 1")

    link = ET.SubElement(root, "link", {"name": f"segment{i}b"})
    add_visual(link, "shaft", placement=placement, rgba="1 0 0 1")
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

    match i:
        case 0:
            add_joint_tendons(
                prev_link,
                first_link,
                link,
                [
                    (0, "top"),
                    (0, "top"),
                    (0, "top"),
                    (0, "top"),
                    (1, "falling"),
                    (2, "falling"),
                    (3, "falling"),
                    (4, "rising"),
                    (5, "rising"),
                    (6, "rising"),
                    (7, "bottom"),
                    (7, "bottom"),
                    (7, "bottom"),
                    (7, "bottom"),
                ],
                Placement(Vector(0, 0, ARM_START_Z), Rotation(0, 0, 0)),
                Placement(Vector(0, 0, ARM_START_Z), Rotation(0, 0, 0)),
                True,
                False,
                [
                    None,
                    None,
                    None,
                    None,
                    (7, 4, 4),
                    (8, 5, 5),
                    (4, 6, -1),
                    (5, 7, -2),
                    (6, 8, -3),
                    (9, 9, 6),
                    (10, 10, -7),
                    (11, 11, -7),
                    (12, 12, -7),
                    (13, 13, -7)
                ],
            )
        case 1:
            add_non_direction_changing_tendons([
                None, 4, 4, 4, 4, -5, 1, 2, 3, -6, None, None, None, None
            ])
            add_joint_tendons(
                prev_link,
                first_link,
                link,
                [
                    None,
                    (4, "top"),
                    (4, "top"),
                    (4, "top"),
                    (4, "top"),
                    (5, "falling"),
                    (1, "rising"),
                    (2, "rising"),
                    (3, "rising"),
                    (6, "falling"),
                    (7, "bottom"),
                    (7, "bottom"),
                    (7, "bottom"),
                    (7, "bottom"),
                ],
                SEGMENTS[i].placement.multiply(
                    Placement(
                        Vector(
                            0,
                            0,
                            0,  # JOINT_PULLEY_SPACING * (i + 1),
                        ),
                        Rotation(0, 0, 0),
                    )
                ),
                None,
                False,
                True,
            )
        case 2:
            add_non_direction_changing_tendons([
                None, None, None, None, None, 5, -1, -2, -3, -6, -6, -6, -6, None
            ])
            add_joint_tendons(
                prev_link,
                first_link,
                link,
                [
                    None,
                    (4, "top"),
                    (4, "top"),
                    (4, "top"),
                    (4, "top"),
                    (5, "rising"),
                    (1, "falling"),
                    (2, "falling"),
                    (3, "falling"),
                    (6, "bottom"),
                    (6, "bottom"),
                    (6, "bottom"),
                    (6, "bottom"),
                    None,
                ],
                None,
                SEGMENTS[i].placement,
                True,
                False,
            )
        case 3:
            add_joint_tendons(
                prev_link,
                first_link,
                link,
                [
                    None,
                    None,
                    (5, "top"),
                    (5, "top"),
                    (5, "top"),
                    (5, "top"),
                    (1, "rising"),
                    (2, "rising"),
                    (3, "bottom"),
                    (6, "bottom"),
                    (6, "bottom"),
                    (6, "bottom"),
                    (6, "bottom"),
                    None,
                ],
                SEGMENTS[i].placement,
                None,
                False,
                True,
                [
                    None,
                    None,
                    (2, 2, 5),
                    (3, 3, 5),
                    (4, 4, 5),
                    (5, 5, 5),
                    (6, 6, 1),
                    (7, 7, 2),
                    (8, 8, -3),
                    None,
                    None,
                    None,
                    None,
                    None,
                ],
            )
        case 4:
            add_joint_tendons(
                prev_link,
                first_link,
                link,
                [
                    None,
                    None,
                    (5, "top"),
                    (5, "top"),
                    (5, "top"),
                    (5, "top"),
                    (1, "top"),
                    (2, "top"),
                    (3, "bottom"),
                    (3, "bottom"),
                    (3, "bottom"),
                    (3, "bottom"),
                    None,
                    None,
                ],
                None,
                SEGMENTS[i].placement,
                True,
                False,
                [
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    (8, -4, -3),
                    (9, -3, -3),
                    (10, -2, -3),
                    (11, -1, -3),
                    (6, -7, 1),
                    (7, -6, 2),
                    None,
                    None,
                ],
            )
        case 5:
            add_joint_tendons(
                prev_link,
                first_link,
                link,
                [
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    (1, "top"),
                    (2, "top"),
                    None,
                    (3, "bottom"),
                    (3, "bottom"),
                    (3, "bottom"),
                    (3, "bottom"),
                    None,
                ],
                None,
                None,  # SEGMENTS[i].placement,
                False,
                True,
                [],
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
    prev_link = link

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
