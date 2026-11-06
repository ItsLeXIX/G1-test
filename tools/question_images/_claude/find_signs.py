# Lists Commons files named "CA-ON road sign ..." (query only, no downloads).
import json, urllib.request, urllib.parse, os
UA = {"User-Agent": "G1QuestionImages/1.0 (Ontario driver-test study app; asset build)"}
out = []
cont = {}
while True:
    q = {"action": "query", "list": "allimages", "aiprefix": "CA-ON_road_sign", "ailimit": "500",
         "aiprop": "url|size", "format": "json", **cont}
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q), headers=UA)
    d = json.load(urllib.request.urlopen(req, timeout=30))
    out += d["query"]["allimages"]
    if "continue" not in d:
        break
    cont = d["continue"]
dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commons_ca_on.json")
json.dump(out, open(dst, "w"), indent=1)
print("FOUND", len(out), "->", dst)
