"""Scene templates. Each module exposes build(spec) and sets up camera,
lighting and geometry for one kind of picture."""
import importlib

NAMES = [
    "roadside",             # sign on a post beside a road (suburban / rural / construction)
    "overhead",             # sign hung over the lanes (city mast arm / highway truss)
    "city_street",          # downtown street with buildings, sign at the curb
    "parking_lot",          # parking lot in front of a building
    "highway",              # 400-series freeway, sign on the right shoulder
    "guide_sign",           # big green guide / distance sign beside a highway
    "vehicle_rear",         # following a vehicle (SMV wagon, car at a stop / one-way)
    "hand_signal",          # driver's arm out of the window, seen from behind-left
    "railway_crossing",     # level crossing with flashing-light signal and tracks
    "intersection_aerial",  # high view of a 4-way intersection with path arrows
    "marking_aerial",       # high view of a lane with a pavement marking
]


def get(name):
    if name not in NAMES:
        raise KeyError(f"unknown scene template {name!r}; choose from {NAMES}")
    return importlib.import_module(f"{__name__}.{name}")
