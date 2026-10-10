#!/usr/bin/env python3
"""Turn cached ESPN raw data into data/tracker.json. No values are invented; everything traces to data/raw/*."""
import json, os, datetime
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(ROOT, "data", "raw")
ET = ZoneInfo("America/New_York")
def L(n): return json.load(open(os.path.join(RAW, n + ".json")))
man = json.load(open(os.path.join(ROOT, "data", "manifest.json")))
team = L("team")["team"]; sched = L("schedule"); stand = L("standings_b1g")
tstats = L("team_statistics")["results"]; core_rec = L("core_record_120"); lead = L("core_leaders_120")
grp81 = L("core_group_81")
MD = "120"

def sv(stats, name, typ=None):
    for x in stats:
        if x.get("name") == name and (typ is None or x.get("type") == typ): return x
    return None

# ---- standings ----
rows = []
for e in stand["standings"]["entries"]:
    st = e["stats"]; t = e["team"]
    g = lambda typ: next((x for x in st if x.get("type") == typ), {})
    rows.append({"id": t["id"], "abbr": t["abbreviation"], "name": t["displayName"], "short": t.get("shortDisplayName") or t["location"],
                 "location": t["location"], "rank": (t.get("rank") if t.get("rank") not in (None, 99) else None),
                 "seed": int(float(g("playoffseed").get("value", 0) or 0)),
                 "conf": g("vsconf").get("displayValue"), "overall": g("total").get("displayValue"),
                 "home": g("homerecord").get("displayValue"), "away": g("awayrecord").get("displayValue"),
                 "pf": g("pointsfor").get("value"), "pa": g("pointsagainst").get("value"),
                 "diff": g("pointdifferential").get("value"), "streak": g("streak").get("displayValue")})
rows.sort(key=lambda r: r["seed"])
byid = {r["id"]: r for r in rows}
def wl(s):
    w, l = (int(x) for x in s.split("-")[:2]); return w, l

# ---- games ----
def et(iso):
    return datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc).astimezone(ET)
games = []
for ev in sched["events"]:
    c = ev["competitions"][0]
    me = next(x for x in c["competitors"] if x["team"]["id"] == MD)
    op = next(x for x in c["competitors"] if x["team"]["id"] != MD)
    d = et(ev["date"]); tv = ev.get("timeValid", True) and c.get("timeValid", True)
    st = c["status"]["type"]
    summ = L("summary_" + ev["id"])
    rank = op.get("curatedRank", {}).get("current")
    g = {"id": ev["id"], "week": ev["week"]["number"], "date_et": d.strftime("%a %b %-d"), "iso": ev["date"],
         "time_et": (d.strftime("%-I:%M %p ET") if tv else "Time TBA"), "time_valid": bool(tv),
         "home": me["homeAway"] == "home", "neutral": c.get("neutralSite", False),
         "venue": c.get("venue", {}).get("fullName"), "city": ", ".join(filter(None, [c.get("venue", {}).get("address", {}).get("city"), c.get("venue", {}).get("address", {}).get("state")])),
         "tv": [b["media"]["shortName"] for b in c.get("broadcasts", [])],
         "opp": {"id": op["team"]["id"], "abbr": op["team"]["abbreviation"], "name": op["team"]["displayName"],
                 "location": op["team"]["location"], "nickname": op["team"].get("nickname"),
                 "rank": rank if rank and rank != 99 else None},
         "conference": op["team"]["id"] in byid, "status": st["name"], "final": bool(st.get("completed"))}
    if g["opp"]["id"] in byid:
        g["opp"]["overall"] = byid[g["opp"]["id"]]["overall"]; g["opp"]["conf"] = byid[g["opp"]["id"]]["conf"]
    if g["final"]:
        ms, os_ = int(me["score"]["displayValue"]), int(op["score"]["displayValue"])
        g.update({"md_score": ms, "opp_score": os_, "win": bool(me.get("winner")), "result": ("W" if me.get("winner") else "L")})
        h = summ["header"]["competitions"][0]
        g["linescores"] = {x["team"]["abbreviation"]: [int(q["displayValue"]) for q in x.get("linescores", [])] for x in h["competitors"]}
        g["headline"] = (summ.get("article") or {}).get("headline")
        bx = {t["team"]["id"]: {s["label"]: s["displayValue"] for s in t["statistics"]} for t in summ["boxscore"]["teams"]}
        keys = ["Total Yards", "Passing", "Rushing", "1st Downs", "3rd down efficiency", "Turnovers", "Penalties", "Possession"]
        g["box"] = {"md": {k: bx[MD].get(k) for k in keys}, "opp": {k: bx[g["opp"]["id"]].get(k) for k in keys}}
        tops = {}
        for p in summ["boxscore"]["players"]:
            if p["team"]["id"] != MD: continue
            for s in p["statistics"]:
                if s["name"] in ("passing", "rushing", "receiving", "defensive") and s["athletes"]:
                    a = s["athletes"][0]; tops[s["name"]] = {"name": a["athlete"]["displayName"], "line": dict(zip(s["labels"], a["stats"]))}
        g["md_top"] = tops
        g["scoring_plays"] = len(summ.get("scoringPlays", []))
    else:
        pr = summ.get("predictor") or {}
        side = pr.get("homeTeam") if pr.get("homeTeam", {}).get("id") == MD else pr.get("awayTeam")
        g["espn_md_win_pct"] = float(side["gameProjection"]) if side and side.get("gameProjection") else None
        pc = (summ.get("pickcenter") or [])
        g["line"] = {"provider": pc[0]["provider"]["name"], "details": pc[0].get("details"), "ou": pc[0].get("overUnder")} if pc and pc[0].get("details") else None
    games.append(g)

done = [g for g in games if g["final"]]; left = [g for g in games if not g["final"]]
W = sum(g["win"] for g in done); Lo = len(done) - W
recs = {i["type"]: i["summary"] for i in team["record"]["items"]}
# FCS opponents (ESPN group parent 81 == FCS). NCAA bowl rule: only one FCS win per season counts toward the 6.
for g in games:
    g["fcs"] = False
    if not g["conference"]:
        ot = L("opp_team_" + g["opp"]["id"])["team"]
        g["fcs"] = (ot.get("groups") or {}).get("parent", {}).get("id") == "81"
        g["opp"]["summary"] = ot.get("standingSummary")
fcs_wins = sum(1 for g in done if g["fcs"] and g["win"])
W_bowl = W - max(0, fcs_wins - 1)
# ---- bowl math ----
need = max(0, 6 - W_bowl)
probs = [g["espn_md_win_pct"] / 100 for g in left if g.get("espn_md_win_pct") is not None]
dist = [1.0]
for p in probs:
    nd = [0.0] * (len(dist) + 1)
    for k, v in enumerate(dist): nd[k] += v * (1 - p); nd[k + 1] += v * p
    dist = nd
p_bowl = sum(dist[need:]) if len(probs) == len(left) else None
exp_wins = sum(probs)
# simple record-based estimate (log5 on shrunk win%, +/-0.05 home/away) as a second, transparent opinion
mdw, mdl = wl(recs["total"]); a = (mdw + 2) / (mdw + mdl + 4)
for g in left:
    ow, ol = wl(g["opp"]["overall"]); b = (ow + 2) / (ow + ol + 4)
    p = a * (1 - b) / (a * (1 - b) + b * (1 - a)); p = min(0.97, max(0.03, p + (0.05 if g["home"] else -0.05)))
    g["record_model_win_pct"] = round(p * 100, 1)
winnable = sorted(left, key=lambda g: -(g.get("espn_md_win_pct") or 0))
bowl = {"wins": W, "countable_wins": W_bowl, "fcs_wins": fcs_wins, "losses": Lo, "needed_total": 6, "wins_needed": need, "games_left": len(left),
        "max_wins": W_bowl + len(left), "can_lose": len(left) - need,
        "p_bowl_espn_based": round(p_bowl * 100, 1) if p_bowl is not None else None,
        "expected_final_wins": round(W_bowl + exp_wins, 1),
        "win_distribution": [{"final_wins": W_bowl + k, "pct": round(v * 100, 1)} for k, v in enumerate(dist)],
        "winnable_order": [g["id"] for g in winnable]}

# ---- leaders (core leaders endpoint) + box-score sums for cross-check ----
ath = {}
for f in os.listdir(RAW):
    if f.startswith("athlete_"):
        a = json.load(open(os.path.join(RAW, f)))
        ath[a["id"]] = {"name": a["displayName"], "jersey": a.get("jersey"), "pos": (a.get("position") or {}).get("abbreviation"),
                        "class": (a.get("experience") or {}).get("displayValue")}
want = {"passingYards": "Passing yards", "rushingYards": "Rushing yards", "receivingYards": "Receiving yards", "totalTackles": "Tackles",
        "sacks": "Sacks", "interceptions": "Interceptions"}
detail = {"passingYards": "passingLeader", "rushingYards": "rushingLeader", "receivingYards": "receivingLeader"}
cats = {c["name"]: c for c in lead["categories"]}
leaders = []
for k, label in want.items():
    c = cats.get(k)
    if not c: continue
    top = []
    for l in c["leaders"][:3]:
        aid = l["athlete"]["$ref"].split("/athletes/")[1].split("?")[0]
        line = None
        if k in detail:
            dl = next((x for x in cats[detail[k]]["leaders"] if x["athlete"]["$ref"].split("/athletes/")[1].split("?")[0] == aid), None)
            line = dl["displayValue"] if dl else None
        top.append({"athlete_id": aid, **ath.get(aid, {"name": "?"}), "value": l["displayValue"], "line": line})
    leaders.append({"key": k, "label": label, "top": top})

# box-score sums (per-game summaries) for the leader categories, to surface any feed disagreement on the page
bsum = {}
for g in done:
    for p in L("summary_" + g["id"])["boxscore"]["players"]:
        if p["team"]["id"] != MD: continue
        for s in p["statistics"]:
            lab = {"passing": "YDS", "rushing": "YDS", "receiving": "YDS", "defensive": "TOT"}.get(s["name"])
            if not lab: continue
            for a in s["athletes"]:
                d = dict(zip(s["labels"], a["stats"])); k = (s["name"], a["athlete"]["id"])
                bsum[k] = bsum.get(k, 0) + float(d[lab].replace(",", ""))
bmap = {"passingYards": "passing", "rushingYards": "rushing", "receivingYards": "receiving", "totalTackles": "defensive"}
for l in leaders:
    if l["key"] in bmap:
        for t in l["top"]:
            v = bsum.get((bmap[l["key"]], t["athlete_id"]))
            t["box_sum"] = (int(v) if v is not None and v == int(v) else v)
            t["box_mismatch"] = v is not None and v != float(t["value"].replace(",", ""))

def cat(stats, name): return {x["name"]: x["displayValue"] for x in next(c for c in stats["categories"] if c["name"] == name)["stats"]}
mdS, opS = tstats["stats"], tstats["opponent"]
opS = {"categories": opS} if isinstance(opS, list) else opS
def pack(s):
    p, r, m, sc = cat(s, "passing"), cat(s, "rushing"), cat(s, "miscellaneous"), cat(s, "scoring")
    return {"ppg": sc.get("totalPointsPerGame"), "ypg": p.get("yardsPerGame"), "pass_ypg": p.get("netPassingYardsPerGame"),
            "rush_ypg": r.get("rushingYardsPerGame"), "ypc": r.get("yardsPerRushAttempt"), "third": m.get("thirdDownEff"),
            "third_pct": m.get("thirdDownConvPct"), "penalties": m.get("totalPenaltiesYards"), "giveaways": m.get("totalGiveaways"),
            "takeaways": m.get("totalTakeaways"), "to_diff": m.get("turnOverDifferential"), "sacks": cat(s, "defensive").get("sacks")}
team_stats = {"md": pack(mdS), "opp": pack(opS)}

out = {"generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "fetched_at": man["fetched_at"],
       "season": sched["season"]["year"], "team": {"name": team["displayName"], "summary": team.get("standingSummary"), "records": recs,
       "core_records": {i["type"]: i["summary"] for i in core_rec["items"]}},
       "computed_record": f"{W}-{Lo}", "games": games, "standings": rows, "bowl": bowl, "leaders": leaders, "team_stats": team_stats,
       "fcs_group": {"id": grp81.get("id"), "name": grp81.get("name"), "abbr": grp81.get("abbreviation")},
       "sources": [{"name": f["name"], "url": f["url"], "fetched_at": f["fetched_at"]} for f in man["files"] if f["name"] in ("team", "schedule", "standings_b1g", "team_statistics", "core_record_120", "core_leaders_120")],
       "source_count": len(man["files"])}
json.dump(out, open(os.path.join(ROOT, "data", "tracker.json"), "w"), indent=1)
print("record", out["computed_record"], recs, "bowl", bowl["wins_needed"], "of", bowl["games_left"], "P", bowl["p_bowl_espn_based"], "E", bowl["expected_final_wins"])
for g in winnable: print(g["date_et"], g["opp"]["abbr"], g["opp"]["overall"], "home" if g["home"] else "away", g["espn_md_win_pct"], g["record_model_win_pct"], g["time_et"], g["tv"], g["line"])
for l in leaders: print(l["label"], [(t["name"], t["value"], t.get("pos"), t.get("class")) for t in l["top"]])
print(team_stats); print(out["fcs_group"])
