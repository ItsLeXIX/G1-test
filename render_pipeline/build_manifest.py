"""Build manifest.json for the G1 image re-render.

Reads questions.json for question text / correct answer and merges in the
per-image scene decisions below (made by looking at each current image).
Run:  python build_manifest.py <questions.json> <out manifest.json>
"""
import json, sys

# Shared camera presets (same lens / height across every image of a type)
CAMERAS = {
    "roadside":   {"lens_mm": 35, "height_m": 1.2, "note": "driver eye height, looking down the road; sign right-of-centre, ~12 m ahead, square to camera"},
    "overhead":   {"lens_mm": 35, "height_m": 1.2, "note": "looking up ~12 deg at an overhead span-wire / truss sign, sky behind"},
    "city":       {"lens_mm": 35, "height_m": 1.2, "note": "sidewalk view, buildings behind, sign ~6 m away"},
    "parking":    {"lens_mm": 35, "height_m": 1.2, "note": "facing a parking lot edge with building behind, sign ~5 m away"},
    "vehicle":    {"lens_mm": 35, "height_m": 1.2, "note": "behind a generic unbranded car, ~6 m back"},
    "hand":       {"lens_mm": 35, "height_m": 1.2, "note": "rear-left 3/4 of an unbranded car; driver's arm out the left window"},
    "aerial":     {"lens_mm": 35, "height_m": 18.0, "note": "elevated 3/4 view of an intersection"},
    "topdown":    {"lens_mm": 35, "height_m": 12.0, "note": "near top-down view of lane markings"},
    "highway":    {"lens_mm": 35, "height_m": 1.2, "note": "multi-lane divided road, sign on median or shoulder"},
}

# imageName: (signs, scene, weather, camera preset, extra notes, flag)
# flag = None, or a reason the sign/scene changes vs the current image
E = {
 "1":  (["Road work ahead (orange diamond, worker symbol)"], "roadside", "clear", "roadside", "add cones/barrels far ahead", None),
 "2":  (["Right turn only (white rectangle, curved right arrow, ONLY)"], "roadside", "clear", "roadside", "", None),
 "3":  (["Slow-moving vehicle (orange triangle, red reflective border)"], "vehicle_rear", "clear", "vehicle", "sign mounted on rear of a farm-type or utility vehicle; current image puts it on an SUV — use a tractor/utility vehicle so the meaning is realistic", "scene: SUV -> slow farm/utility vehicle"),
 "4":  (["Hospital (blue square, white H)"], "roadside", "clear", "roadside", "", None),
 "5":  (["No U-turn (white square, red circle/slash)"], "roadside", "clear", "roadside", "", None),
 "6":  (["Airport (green square, white airplane)"], "roadside", "clear", "roadside", "", None),
 "7":  (["Sharp right turn (yellow diamond, 90-degree right arrow)"], "roadside", "clear", "roadside", "road visibly bends right ahead", None),
 "8":  (["No straight through (white square, red circle/slash over up arrow)"], "roadside", "clear", "roadside", "intersection ahead", None),
 "9":  (["Lift/swing bridge ahead (yellow diamond)"], "roadside", "clear", "roadside", "bridge and water visible ahead", None),
 "10": (["Yield (red/white inverted triangle)"], "roadside", "clear", "roadside", "intersection ahead", None),
 "11": (["Generic prohibition symbol: red circle with slash on white square"], "roadside", "clear", "roadside", "", "sign: current is a European round red-ring disc -> Canadian red circle/slash on white square"),
 "12": (["Snowmobiles permitted (white square, green circle, snowmobile)"], "roadside", "snow", "roadside", "rural road with snow banks", "weather: clear -> snow (fits the sign)"),
 "13": (["Detour (orange diamond, DETOUR + right arrow)"], "roadside", "clear", "roadside", "construction barrels near the detour", None),
 "14": (["Traffic signal ahead (yellow diamond, signal symbol)"], "roadside", "clear", "roadside", "traffic lights visible far ahead", None),
 "15": (["No idling (Ontario municipal, white rectangle)"], "parking_lot", "clear", "parking", "", "check: idling signs are municipal by-law signs, not MTO handbook; use Toronto/Ontario municipal artwork"),
 "16": (["Do not block intersection (overhead text sign)"], "overhead", "clear", "overhead", "", "check: confirm Ontario colour (current image is yellow)"),
 "17": (["No passing (white square, red circle/slash over two cars)"], "roadside", "clear", "roadside", "two-lane rural road", None),
 "18": (["Hidden side road right (yellow diamond) + HIDDEN tab"], "roadside", "clear", "roadside", "side road hidden behind trees/hill", None),
 "19": (["No bicycles (white square, red circle/slash over bicycle)"], "city_street", "clear", "city", "", "sign: current is a European round disc -> Ontario square no-bicycles sign"),
 "20": (["Permissive parking with time limit (green P, 30 MIN 9AM-6PM MON-FRI, arrows)"], "parking_lot", "clear", "parking", "street parking bays", None),
 "41": (["RIGHT LANE MUST EXIT (overhead, black/white)"], "overhead", "clear", "overhead", "", None),
 "42": (["Hidden school bus stop ahead (yellow diamond)"], "roadside", "clear", "roadside", "crest or curve hides what's ahead", None),
 "43": (["Yield (red/white inverted triangle)"], "roadside", "clear", "roadside", "same sign as #10, different viewpoint — merging road", None),
 "44": (["Railway crossing signal: crossbuck + flashing red lights"], "railway_crossing", "clear", "roadside", "tracks crossing the road, signal mast on right", None),
 "45": (["Do not enter (white square, red circle, white bar)"], "city_street", "clear", "city", "one-way street entrance", "sign: current is a European round disc -> Canadian Do Not Enter"),
 "46": (["Divided highway begins (yellow diamond)"], "highway", "clear", "highway", "median starts ahead", None),
 "47": (["No pedestrians (white square, red circle/slash over walker)"], "roadside", "clear", "roadside", "", "sign: current is a European round disc -> Canadian square version"),
 "48": (["Two-way left-turn lane (overhead black/white) + matching pavement arrows"], "overhead", "clear", "highway", "centre lane with yellow solid/broken lines and opposing arrows", None),
 "49": (["Accessible parking (blue square, wheelchair)"], "parking_lot", "clear", "parking", "accessible bay with painted symbol", "scene: road -> parking lot (fits the sign)"),
 "50": (["Winding road (yellow diamond)"], "roadside", "clear", "roadside", "road winding ahead", None),
 "51": (["Water may flow over road (yellow diamond)"], "roadside", "rain", "roadside", "low dip, wet pavement", "weather: clear -> rain/wet"),
 "52": (["Generic permissive symbol: green circle on white square"], "roadside", "clear", "roadside", "", None),
 "53": (["No right turn on red (white rectangle)"], "overhead", "clear", "overhead", "traffic signal beside it", None),
 "54": (["Object/hazard marker (black/yellow diagonal stripes)"], "highway", "clear", "highway", "marker on median nose; stripe direction must point to pass side", None),
 "55": (["Reserved lane: buses/taxis/cyclists, times shown (overhead diamond sign)"], "overhead", "clear", "overhead", "", "check: confirm exact vehicle list on Ontario artwork"),
 "56": (["Keep right of obstruction (white rectangle)"], "highway", "clear", "highway", "median island ahead", None),
 "57": (["School crossing (yellow pentagon) + AHEAD tab"], "city_street", "clear", "city", "school building nearby", None),
 "58": (["Hand signal: left turn (arm straight out)"], "hand_signal", "clear", "hand", "arm straight out horizontally", "scene: remove car brand lettering"),
 "59": (["Distance sign (green, white text, Ontario place names)"], "highway", "clear", "highway", "", "sign: current is a US (Nevada) sign -> Ontario distance sign"),
 "60": (["Speed limit 50 ahead (white rectangle, arrow, 50)"], "roadside", "clear", "roadside", "", None),
 "81": (["School zone 40 km/h when flashing (pentagon + MAXIMUM 40 km/h WHEN FLASHING tabs, two yellow beacons)"], "city_street", "clear", "city", "", "scene: current is a flat diagram on white -> real school-zone street"),
 "82": (["Community safety zone, fines increased (white rectangle)"], "city_street", "clear", "city", "", None),
 "83": (["Bus entrance on right (yellow diamond)"], "roadside", "clear", "roadside", "bus driveway visible on right", None),
 "84": (["Two-way traffic (yellow diamond)"], "roadside", "clear", "roadside", "divided road ends into two-way", None),
 "85": (["Hand signal: right turn (arm bent up)"], "hand_signal", "clear", "hand", "forearm pointing up", "scene: remove car brand lettering"),
 "86": (["Traffic control person ahead (orange diamond)"], "roadside", "clear", "roadside", "work zone ahead", None),
 "87": (["Pavement ends (yellow diamond)"], "roadside", "clear", "roadside", "asphalt turns to gravel ahead", None),
 "88": (["Lane designation sign (overhead, arrows per lane)"], "city_street", "clear", "city", "matching pavement arrows in each lane", "check: current sign is dark brown/black; Ontario lane-designation signs are black on white"),
 "89": (["Narrow bridge (yellow diamond)"], "roadside", "clear", "roadside", "narrow bridge ahead", None),
 "90": (["Curve left (yellow diamond)"], "roadside", "clear", "roadside", "road gently curves left", None),
 "91": (["Steep hill (yellow diamond) with % tab"], "roadside", "clear", "roadside", "road drops downhill ahead", None),
 "92": (["Railway crossing ahead, angled (yellow diamond)"], "roadside", "clear", "roadside", "tracks visible ahead", None),
 "93": (["Destination direction sign (green, three lines)"], "roadside", "clear", "roadside", "", "scene: current is a flat crop -> roadside scene"),
 "94": (["Bicycle crossing (yellow diamond)"], "roadside", "clear", "roadside", "bike path crossing ahead", None),
 "95": (["STOP FOR SCHOOL BUS WHEN SIGNALS FLASHING (white rectangle)"], "roadside", "clear", "roadside", "", "scene: overhead -> roadside (this sign is post-mounted at province borders)"),
 "96": (["Road splits / divided highway begins? (yellow diamond)"], "roadside", "clear", "roadside", "", "UNSURE: current image looks like a lane-addition sign, not 'road splits' — need to confirm which sign the answer means"),
 "97": (["HOV lane 2+ (overhead diamond sign)"], "overhead", "clear", "overhead", "", None),
 "98": (["No left turn (white square, red circle/slash)"], "roadside", "clear", "roadside", "intersection ahead", None),
 "99": (["Merge (yellow diamond)"], "highway", "clear", "highway", "on-ramp merging from right", None),
 "100":(["Low clearance 3.8 m (yellow diamond)"], "roadside", "clear", "roadside", "underpass ahead", None),
 "101":(["Reverse curve right-left (yellow diamond)"], "roadside", "clear", "roadside", "S-curve ahead", None),
 "102":(["Curve warning (yellow diamond) + advisory speed tab (yellow, number km/h)"], "roadside", "clear", "roadside", "rural curve", "sign: current tab says 'XX km/h' -> real number (proposed 40)"),
 "103":(["Falling rock (yellow diamond)"], "roadside", "clear", "roadside", "rock cut beside road", None),
 "104":(["Permit parking only: no-parking symbol + accessible symbol + BY PERMIT ONLY"], "parking_lot", "clear", "parking", "", None),
 "105":(["Stop ahead (yellow diamond, stop symbol + arrow)"], "roadside", "clear", "roadside", "", None),
 "106":(["Reserved bicycle lane (white, diamond + bicycle + down arrow)"], "city_street", "clear", "city", "painted bike lane", None),
 "107":(["Narrow road (yellow diamond)"], "roadside", "clear", "roadside", "road narrows ahead", None),
 "108":(["Intersection ahead (yellow diamond, cross)"], "roadside", "clear", "roadside", "crossroad ahead", None),
 "109":(["Divided highway ends (yellow diamond)"], "highway", "clear", "highway", "median ends ahead", None),
 "110":(["Deer crossing (yellow diamond) on large panel with 'Next 15 km' tab"], "roadside", "dusk", "roadside", "rural, forest edge", "scene: current is a flat crop -> rural road at dusk"),
 "111":(["Railway crossing ahead (yellow diamond, tracks cross)"], "roadside", "clear", "roadside", "tracks ahead", None),
 "112":(["Bump/uneven pavement (yellow diamond)"], "roadside", "clear", "roadside", "", None),
 "113":(["Snowmobile crossing (yellow diamond)"], "roadside", "snow", "roadside", "trail crossing in snow", "weather: clear -> snow"),
 "114":(["Pedestrian crossover (white, PEDESTRIAN + X)"], "city_street", "clear", "city", "crossover markings (ladder/X) on road", None),
 "115":(["Bicycle route (white square, green circle, bicycle)"], "roadside", "clear", "roadside", "", None),
 "116":(["Fire truck entrance on right (yellow diamond)"], "roadside", "clear", "roadside", "fire hall driveway on right", None),
 "117":(["RED LIGHT PHOTO ENFORCED (white rectangle with signal)"], "overhead", "night", "overhead", "signalised intersection", "weather: clear -> night"),
 "118":(["No standing anytime (red on white, arrows)"], "parking_lot", "clear", "parking", "", None),
 "119":(["SLOWER TRAFFIC KEEP RIGHT (white rectangle)"], "highway", "clear", "highway", "", None),
 "120":(["Slippery when wet (yellow diamond)"], "roadside", "rain", "roadside", "wet pavement", "weather: clear -> rain"),
 "141":(["Survey crew (orange diamond)"], "roadside", "clear", "roadside", "", "check: current sign is square-ish; Ontario survey crew sign is a diamond"),
 "142":(["SCHOOL BUS LOADING ZONE + arrow (white rectangle)"], "city_street", "clear", "city", "", None),
 "143":(["Hand signal: slow/stop (arm bent down)"], "hand_signal", "clear", "hand", "forearm pointing down", "scene: remove car brand lettering"),
 "144":(["Checkerboard + arrow (yellow/black), sharp turn"], "roadside", "clear", "roadside", "T-intersection or sharp bend", None),
 "145":(["Passing lane ahead (white/black)"], "highway", "clear", "highway", "", None),
 "146":(["Right lane ends (yellow diamond)"], "highway", "clear", "highway", "", None),
 "147":(["HOV do not cross (overhead white)"], "overhead", "clear", "overhead", "", None),
 "148":(["MAXIMUM 80 km/h (white rectangle)"], "highway", "clear", "highway", "", None),
 "149":(["Stop (red octagon)"], "roadside", "clear", "roadside", "car stopped at a stop line", None),
 "150":(["No left turn during times shown (white rectangle)"], "overhead", "clear", "overhead", "", None),
 "151":(["One way (black/white arrow)"], "city_street", "clear", "city", "", None),
 "152":(["Paved/grooved surface (orange diamond)"], "roadside", "clear", "roadside", "grooved pavement ahead", None),
 "153":(["No stopping (white, red circle/slash over stop hand, double arrow)"], "city_street", "clear", "city", "", "check: confirm Ontario symbol artwork"),
 "154":(["Roundabout ahead (yellow diamond) + 300 m tab"], "roadside", "clear", "roadside", "", None),
 "155":(["Chevron alignment (yellow/black, pointing left)"], "roadside", "clear", "roadside", "sharp left curve", None),
 "156":(["Pedestrian crossing ahead (yellow diamond)"], "roadside", "clear", "roadside", "", None),
 "157":(["Lane closed / shift (orange diamond, diagonal arrow)"], "roadside", "clear", "roadside", "construction barrels closing a lane", None),
 "158":(["CONSTRUCTION 1 km (orange diamond, arrow)"], "roadside", "clear", "roadside", "", None),
 "159":(["KEEP RIGHT EXCEPT TO PASS (white rectangle)"], "highway", "clear", "highway", "", "scene: overhead -> highway shoulder"),
 "160":(["Sharrow pavement marking (bicycle + chevrons)"], "pavement_marking", "clear", "topdown", "", None),
 "161":(["No sign: uncontrolled intersection, two cars with path arrows"], "aerial_intersection", "clear", "aerial", "blue car straight, red car turning left; arrows as 3D ribbons", None),
}

def main(qpath, out):
    qs = json.load(open(qpath, encoding="utf-8"))["questions"]
    by = {}
    for q in qs:
        if q.get("imageName") and q["language"] == "en":
            by.setdefault(q["imageName"], []).append(q)
    missing = set(by) - set(E)
    assert not missing, f"no scene decision for {missing}"
    entries = []
    for name in sorted(by, key=int):
        signs, scene, weather, cam, notes, flag = E[name]
        q = by[name][0]
        entries.append({
            "imageName": name,
            "questionIds": [x["id"] for x in by[name]],
            "question": q["text"],
            "correctAnswer": q["options"][q["correctIndex"]],
            "signs": signs,
            "scene": scene,
            "weather": weather,
            "camera": dict(CAMERAS[cam], preset=cam),
            "sceneNotes": notes,
            "change": flag,
        })
    json.dump({"version": 1, "resolution": [2400, 1000], "skipped": ["22", "24"],
               "images": entries}, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(len(entries), "entries;", sum(1 for e in entries if e["change"]), "flagged")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
