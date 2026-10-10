#!/usr/bin/env python3
"""Smoke test: cross-checks records/standings between independent ESPN endpoints, leaders vs box scores,
manifest integrity, bowl math, snapshot self-containment and the live server on :4279."""
import json, os, re, hashlib, urllib.request, datetime
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); RAW = os.path.join(ROOT, "data", "raw")
L = lambda n: json.load(open(os.path.join(RAW, n + ".json")))
T = json.load(open(os.path.join(ROOT, "data", "tracker.json")))
passed = failed = 0
def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok); failed += (not ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))

# 1. manifest integrity
man = json.load(open(os.path.join(ROOT, "data", "manifest.json")))
files = {f["name"]: f for f in man["files"]}
check("manifest lists every raw file", set(files) == {f[:-5] for f in os.listdir(RAW)}, f"{len(files)} files")
check("manifest sha256 + url + fetched_at all valid", all(hashlib.sha256(open(os.path.join(ROOT, f["file"]), "rb").read()).hexdigest() == f["sha256"]
      and f["url"].startswith("https://") and f["fetched_at"] and f["http_status"] == 200 for f in man["files"]))

# 2. Maryland record: site team endpoint vs core record endpoint vs standings endpoint vs schedule results
site_total = next(i["summary"] for i in L("team")["team"]["record"]["items"] if i["type"] == "total")
core = {i["type"]: i["summary"] for i in L("core_record_120")["items"]}
st_rows = {}
for e in L("standings_b1g")["standings"]["entries"]:
    st_rows[e["team"]["id"]] = {x["type"]: x.get("displayValue") for x in e["stats"]}
sched = L("schedule")["events"]
fin = [e for e in sched if e["competitions"][0]["status"]["type"]["completed"]]
def md(e): return next(c for c in e["competitions"][0]["competitors"] if c["team"]["id"] == "120")
def opp(e): return next(c for c in e["competitions"][0]["competitors"] if c["team"]["id"] != "120")
w = sum(1 for e in fin if md(e)["winner"]); l = len(fin) - w
sched_rec = f"{w}-{l}"
check("MD overall: site team == core record", site_total == core["total"], f"{site_total} vs {core['total']}")
check("MD overall: core record == standings", core["total"] == st_rows["120"]["total"], f"{core['total']} vs {st_rows['120']['total']}")
check("MD overall: schedule W/L == core record", sched_rec == core["total"], sched_rec)
cw = sum(1 for e in fin if opp(e)["team"]["id"] in st_rows and md(e)["winner"]); cl = sum(1 for e in fin if opp(e)["team"]["id"] in st_rows) - cw
check("MD Big Ten: schedule == core vsconf == standings vsconf", f"{cw}-{cl}" == core["vsconf"] == st_rows["120"]["vsconf"], f"{cw}-{cl} / {core['vsconf']} / {st_rows['120']['vsconf']}")
hw = sum(1 for e in fin if md(e)["homeAway"] == "home" and md(e)["winner"]); hg = sum(1 for e in fin if md(e)["homeAway"] == "home")
check("MD home record: schedule == core == standings", f"{hw}-{hg-hw}" == core["homerecord"] == st_rows["120"]["homerecord"], f"{hw}-{hg-hw}")
pf = sum(int(md(e)["score"]["displayValue"]) for e in fin); pa = sum(int(opp(e)["score"]["displayValue"]) for e in fin)
check("MD points for/against: schedule == standings", (pf, pa) == (int(float(st_rows["120"]["pointsfor"])), int(float(st_rows["120"]["pointsagainst"]))), f"{pf}-{pa}")
# 3. all 18 Big Ten teams: standings endpoint vs each team's core record endpoint
mism = []
for tid, row in st_rows.items():
    c = {i["type"]: i["summary"] for i in L(f"core_record_{tid}")["items"]}
    if (row["total"], row["vsconf"]) != (c.get("total"), c.get("vsconf")): mism.append((tid, row["total"], c.get("total"), row["vsconf"], c.get("vsconf")))
check("Big Ten standings (18 teams) overall+conf: standings == core record", len(st_rows) == 18 and not mism, f"{len(st_rows)} teams, mismatches={mism}")
# opponent records shown on page come from standings
check("upcoming opponents' records on page match standings", all(g["opp"]["overall"] == st_rows[g["opp"]["id"]]["total"] for g in T["games"] if not g["final"]))

# 4. scores: schedule endpoint vs per-game summary header
bad = []
for e in fin:
    h = L("summary_" + e["id"])["header"]["competitions"][0]["competitors"]
    hs = {c["team"]["id"]: int(c["score"]) for c in h}; ss = {c["team"]["id"]: int(c["score"]["displayValue"]) for c in e["competitions"][0]["competitors"]}
    if hs != ss: bad.append(e["id"])
check("final scores: schedule == game summary", not bad, f"{len(fin)} games")

# 5. leaders: core leaders endpoint vs sums of per-game box scores
sums = {}
for e in fin:
    for p in L("summary_" + e["id"])["boxscore"]["players"]:
        if p["team"]["id"] != "120": continue
        for s in p["statistics"]:
            for a in s["athletes"]:
                d = dict(zip(s["labels"], a["stats"])); k = a["athlete"]["id"]
                for cat, lab in (("passing", "YDS"), ("rushing", "YDS"), ("receiving", "YDS"), ("defensive", "TOT")):
                    if s["name"] == cat: sums[(cat, k)] = sums.get((cat, k), 0) + float(d[lab].replace(",", ""))
mp = {"passingYards": "passing", "rushingYards": "rushing", "receivingYards": "receiving", "totalTackles": "defensive"}
for l in T["leaders"]:
    if l["key"] in mp:
        t = l["top"][0]; v = float(t["value"].replace(",", ""))
        bs = sums.get((mp[l["key"]], t["athlete_id"]))
        if l["key"] == "totalTackles":   # tackles are routinely revised after games; allow +/-2 and require the page to disclose any gap
            check(f"leader {l['label']}: core leaders ~ box-score sum within 2 ({t['name']}), gap disclosed on page", bs is not None and abs(bs - v) <= 2 and (bs == v or t.get("box_mismatch")), f"{v:g} vs {bs:g}")
        else:
            check(f"leader {l['label']}: core leaders == box-score sum ({t['name']})", bs == v, f"{v:g} vs {bs:g}")
team_pts = next(x for c in L("team_statistics")["results"]["stats"]["categories"] if c["name"] == "scoring" for x in c["stats"] if x["name"] == "totalPoints")["value"]
check("team statistics total points == schedule points", int(team_pts) == pf, f"{team_pts}")

# 6. bowl math + times
B = T["bowl"]
check("bowl: wins needed = 6 - countable wins", B["wins_needed"] == 6 - B["countable_wins"] and B["countable_wins"] == w - max(0, B["fcs_wins"] - 1))
check("bowl: distribution sums to 100%", abs(sum(d["pct"] for d in B["win_distribution"]) - 100) < 0.6)
check("bowl: P(6+) equals sum of distribution tail", abs(sum(d["pct"] for d in B["win_distribution"] if d["final_wins"] >= 6) - B["p_bowl_espn_based"]) < 0.6)
check("every remaining game has an ESPN predictor value", all(g.get("espn_md_win_pct") is not None for g in T["games"] if not g["final"]))
ET = ZoneInfo("America/New_York"); okt = True
for g in T["games"]:
    if g["time_valid"]:
        d = datetime.datetime.strptime(g["iso"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc).astimezone(ET)
        okt &= g["time_et"] == d.strftime("%-I:%M %p ET") and g["date_et"] == d.strftime("%a %b %-d")
    else: okt &= g["time_et"] == "Time TBA"
check("kickoff times converted UTC -> ET (TBA when ESPN marks time invalid)", okt)

# 7. snapshot self-contained
snap = open(os.path.join(ROOT, "dist", "terps-football-snapshot.html")).read()
ext = re.findall(r'<(?:script|link|img|iframe)[^>]+(?:src|href)=["\']https?:', snap) + re.findall(r'url\(["\']?https?:', snap)
check("snapshot has no external scripts/styles/images/fonts", not ext, f"{len(snap)//1024} KB")
check("snapshot embeds data + fonts", '"computed_record"' in snap and ("font/ttf;base64" in snap or "data:font/ttf;base64" in snap))

# 8. live server
try:
    h = json.load(urllib.request.urlopen("http://127.0.0.1:4279/api/health", timeout=5))
    page = urllib.request.urlopen("http://127.0.0.1:4279/", timeout=5).read().decode()
    api = json.load(urllib.request.urlopen("http://127.0.0.1:4279/api/data", timeout=5))
    check("server :4279 health + page + api", h.get("ok") and "Terps" in page and api["team"]["core_records"]["total"] == core["total"])
except Exception as e:
    check("server :4279 reachable", False, str(e))
print(f"\n{passed}/{passed+failed} passed")
open(os.path.join(ROOT, "tests", "last_run.txt"), "w").write(f"{datetime.datetime.now().astimezone().isoformat(timespec='seconds')} {passed}/{passed+failed} passed\n")
raise SystemExit(1 if failed else 0)
