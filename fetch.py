#!/usr/bin/env python3
"""Fetch real ESPN public data for Maryland football (ESPN team id 120) into data/raw + data/manifest.json."""
import json, hashlib, urllib.request, datetime, os, sys, time
ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "data", "raw")
os.makedirs(RAW, exist_ok=True)
S = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
C = "https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/2026/types/2"
manifest = {"source": "ESPN public site + core APIs", "team": "Maryland Terrapins (ESPN id 120)", "files": []}

def get(name, url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TokenMax terps-football"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read(); status = r.status
            break
        except Exception as e:
            if attempt == 2: raise
            time.sleep(1.5)
    fetched = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    path = os.path.join(RAW, name + ".json")
    open(path, "wb").write(body)
    manifest["files"].append({"name": name, "file": "data/raw/" + name + ".json", "url": url, "fetched_at": fetched,
                              "http_status": status, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
    print(f"{status} {len(body):>8} {name}")
    return json.loads(body)

team = get("team", f"{S}/teams/120")
sched = get("schedule", f"{S}/teams/120/schedule")
stand = get("standings_b1g", "https://site.api.espn.com/apis/v2/sports/football/college-football/standings?group=5")
get("team_statistics", f"{S}/teams/120/statistics")
get("core_record_120", f"{C}/teams/120/record")
lead = get("core_leaders_120", f"{C}/teams/120/leaders")
get("core_group_81", f"{C}/groups/81")
for e in sched["events"]:
    get(f"summary_{e['id']}", f"{S}/summary?event={e['id']}")
# team endpoint for non-Big Ten opponents (to read their ESPN group, e.g. FCS)
b1g = {e["team"]["id"] for e in stand["standings"]["entries"]}
for e in sched["events"]:
    for comp in e["competitions"][0]["competitors"]:
        tid = comp["team"]["id"]
        if tid not in b1g: get(f"opp_team_{tid}", f"{S}/teams/{tid}")
# core record for every Big Ten team (independent endpoint for the standings cross-check)
for ent in stand["standings"]["entries"]:
    tid = ent["team"]["id"]
    if tid != "120":
        get(f"core_record_{tid}", f"{C}/teams/{tid}/record")
# athletes referenced by top-3 leaders (names for the core leaders endpoint)
seen = set()
for cat in lead["categories"]:
    for l in cat["leaders"][:3]:
        ref = l["athlete"]["$ref"].replace("http://", "https://")
        aid = ref.split("/athletes/")[1].split("?")[0]
        if aid not in seen:
            seen.add(aid); get(f"athlete_{aid}", ref)
manifest["fetched_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
json.dump(manifest, open(os.path.join(ROOT, "data", "manifest.json"), "w"), indent=1)
print("manifest:", len(manifest["files"]), "files")
