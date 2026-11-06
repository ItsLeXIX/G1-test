"""World lighting, weather presets, camera framing and render settings.

One look for every image: a physical sky + sun from behind the camera's left
shoulder (so sign faces are front-lit), AgX colour, 50 mm lens at driver
eye height, shallow depth of field focused on the sign.
"""
import math

import bpy
from mathutils import Vector

from . import common as C
from . import realism

ASPECT = (2400, 1000)          # 2.4 : 1, the app's image ratio
EYE_HEIGHT = 1.3               # driver eye height in a car (m)

WEATHER = {
    #            sun elev, sun strength, sky strength, overcast colour
    "clear":    dict(sun_elev=38, sun=4.5, sky=0.12, overcast=None),
    "overcast": dict(sun_elev=50, sun=0.0, sky=0.0, overcast=(0.62, 0.66, 0.72), strength=1.4),
    "rain":     dict(sun_elev=50, sun=0.0, sky=0.0, overcast=(0.42, 0.45, 0.5), strength=1.0),
    "snow":     dict(sun_elev=50, sun=0.0, sky=0.0, overcast=(0.78, 0.8, 0.84), strength=1.6),
    "night":    dict(sun_elev=-10, sun=0.0, sky=0.0, overcast=(0.004, 0.006, 0.012), strength=1.0),
}


def _sun_dir(elev_deg, az_deg):
    el, az = math.radians(elev_deg), math.radians(az_deg)
    return Vector((-math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))


def world(weather="clear", sun_azimuth=150.0):
    """sun_azimuth: degrees around Z from +Y (straight ahead), positive
    to the left. 150 puts the sun behind the camera on its left."""
    # "dusk" (and any other weather only the HDRI table knows) uses the clear-sky
    # fallback settings; the HDRI sets the actual light
    w = WEATHER.get(weather, WEATHER["clear"])
    if realism.enabled() and weather != "night":
        realism.hdri_world(weather, sun_azimuth)
        return w
    sun_d = _sun_dir(w["sun_elev"], sun_azimuth)
    wd = bpy.data.worlds.new("World")
    bpy.context.scene.world = wd
    wd.use_nodes = True
    nt = wd.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    if w["overcast"] is None:
        sky = nt.nodes.new("ShaderNodeTexSky")
        types = [i.identifier for i in sky.bl_rna.properties["sky_type"].enum_items]
        for t in ("MULTIPLE_SCATTERING", "NISHITA", "SINGLE_SCATTERING", "HOSEK_WILKIE"):
            if t in types:
                sky.sky_type = t
                break
        if hasattr(sky, "sun_disc"):
            sky.sun_disc = False          # the Sun lamp provides the sun
        if hasattr(sky, "sun_elevation"):
            sky.sun_elevation = math.radians(w["sun_elev"])
            sky.sun_rotation = math.atan2(sun_d.y, sun_d.x)
        for attr, v in (("air_density", 1.0), ("aerosol_density", 1.5), ("dust_density", 1.5), ("ozone_density", 1.0)):
            if hasattr(sky, attr):
                setattr(sky, attr, v)
        nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = w["sky"]
    else:
        # simple vertical gradient: brighter at the horizon, darker above
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        c = w["overcast"]
        ramp.color_ramp.elements[0].position = 0.5
        ramp.color_ramp.elements[0].color = (*[v * 1.08 for v in c], 1)
        ramp.color_ramp.elements[1].color = (*[v * 0.8 for v in c], 1)
        nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = w.get("strength", 1.0)
    if w["sun"] > 0:
        sd = bpy.data.lights.new("Sun", "SUN")
        sd.energy = w["sun"]
        sd.angle = math.radians(0.6)
        sd.color = (1.0, 0.96, 0.9)
        sun = C.link(bpy.data.objects.new("Sun", sd))
        # light travels along the object's -Z, i.e. away from the sun
        sun.rotation_euler = (-sun_d).to_track_quat("-Z", "Y").to_euler()
    return w


def camera(loc=(1.75, 0.0, EYE_HEIGHT), lens=50.0):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36.0
    cd.clip_start = 0.1
    cd.clip_end = 4000
    cam = C.link(bpy.data.objects.new("Cam", cd))
    cam.location = loc
    bpy.context.scene.camera = cam
    return cam


def frame(cam, target, screen=(0.64, 0.6), focus=None, fstop=1.8):
    """Aim so world point `target` lands at normalised screen position
    `screen` (0..1 from left, 0..1 from bottom), then focus on it."""
    cam_loc = Vector(cam.location)
    t = Vector(target)
    look = (t - cam_loc).normalized()
    cd = cam.data
    w, h = ASPECT
    half_w = math.atan(cd.sensor_width / 2 / cd.lens)
    half_h = math.atan(math.tan(half_w) * h / w)
    du = math.atan((screen[0] - 0.5) * 2 * math.tan(half_w))
    dv = math.atan((screen[1] - 0.5) * 2 * math.tan(half_h))
    yaw = math.atan2(-look.x, look.y) + du       # heading of the look vector
    pitch = math.asin(max(-1, min(1, look.z))) - dv
    cam.rotation_euler = (math.pi / 2 + pitch, 0.0, yaw)
    cd.dof.use_dof = True
    cd.dof.focus_distance = (focus or (t - cam_loc).length)
    cd.dof.aperture_fstop = fstop


def headlights(cam, target, strength=2500):
    """Night: two spots from the car toward the sign so its
    retroreflective sheeting reads bright, as it does in real life."""
    for dx in (-0.75, 0.75):
        sd = bpy.data.lights.new("Headlight", "SPOT")
        sd.energy = strength
        sd.spot_size = math.radians(40)
        sd.spot_blend = 0.6
        sd.color = (1.0, 0.95, 0.85)
        ob = C.link(bpy.data.objects.new("Headlight", sd))
        ob.location = (cam.location.x + dx, cam.location.y + 1.5, 0.7)
        d = Vector(target) - Vector(ob.location)
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def render_settings(quality="preview"):
    sc = bpy.context.scene
    try:
        sc.render.engine = "CYCLES"
    except TypeError as e:
        print("engine:", e)
    cy = sc.cycles
    prefs = bpy.context.preferences.addons.get("cycles")
    if prefs:
        cp = prefs.preferences
        for t in ("OPTIX", "CUDA", "METAL", "HIP", "ONEAPI"):
            try:
                cp.compute_device_type = t
                cp.get_devices()
                if any(d.type != "CPU" for d in cp.devices):
                    for d in cp.devices:
                        d.use = True
                    cy.device = "GPU"
                    print("render device:", t)
                    break
            except TypeError:
                continue
    q = {
        # samples, resolution %; preview is laptop-safe (~960x400)
        "preview": (24, 40),
        "draft":   (96, 100),
        "final":   (384, 100),
    }[quality]
    cy.samples = q[0]
    cy.use_adaptive_sampling = True
    cy.use_denoising = True
    cy.max_bounces = 6
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 3
    cy.transmission_bounces = 4
    cy.transparent_max_bounces = 8
    if hasattr(cy, "tile_size"):
        cy.use_auto_tile = True
        cy.tile_size = 512                 # tiles keep peak memory low
    if hasattr(cy, "texture_limit_render"):
        cy.texture_limit_render = "2048"
    sc.render.use_persistent_data = False
    sc.render.resolution_x, sc.render.resolution_y = ASPECT
    sc.render.resolution_percentage = q[1]
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    # Standard, no look, no exposure: the only transform under which the sign
    # faces' emission reproduces the official artwork colours 1:1. Scene
    # brightness is set with the HDRI strength instead.
    vs = sc.view_settings
    sc.display_settings.display_device = "sRGB"
    vs.view_transform = "Standard"
    vs.look = "None"
    vs.exposure = 0.0
    vs.gamma = 1.0
