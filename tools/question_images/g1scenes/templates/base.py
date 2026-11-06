"""Setup shared by every template."""
from .. import common as C
from .. import env as E
from .. import signs as S


def setup(spec, quality):
    C.reset()
    E.render_settings(quality)
    weather = spec.get("weather", "clear")
    E.world(weather, spec.get("sun_azimuth", 150.0))
    return weather, {
        "wet": 1.0 if weather == "rain" else spec.get("wet", 0.0),
        "snow": 1.0 if weather == "snow" else 0.0,
        "night": weather == "night",
    }


def sign_items(spec):
    """spec["sign"] = [[artwork, width_m], ...] listed top to bottom."""
    return [tuple(i) for i in spec["sign"]]


def finish(cam, target, spec, look):
    E.frame(cam, target, tuple(spec.get("screen", (0.64, 0.6))), fstop=spec.get("fstop", 1.8))
    if look["night"]:
        E.headlights(cam, target)


__all__ = ["setup", "sign_items", "finish", "S"]
