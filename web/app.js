(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const fmtTime = (iso) =>
    new Date(iso).toLocaleString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) + " ET";

  function fail(m) {
    $("app").innerHTML = "<p style='padding:40px;color:#f87171'>Tracker data unavailable. " + esc(m) + "</p>";
  }

  function boot(D, N) {
  N = N || {};
  if (!D) { fail("empty tracker"); return; }

  const G = D.games,
    done = G.filter((g) => g.final),
    left = G.filter((g) => !g.final),
    B = D.bowl,
    cr = D.team.core_records;
  const md = D.standings.find((s) => s.id === "120");

  /* screen nav */
  const nav = $("screen-nav");
  nav.addEventListener("click", (e) => {
    const btn = e.target.closest(".sn");
    if (!btn) return;
    const name = btn.dataset.screen;
    nav.querySelectorAll(".sn").forEach((b) => {
      b.classList.toggle("on", b === btn);
      b.setAttribute("aria-selected", b === btn ? "true" : "false");
    });
    document.querySelectorAll(".screen").forEach((s) => {
      const on = s.id === "screen-" + name;
      s.classList.toggle("on", on);
      s.hidden = !on;
    });
    history.replaceState(null, "", "#"+name);
  });
  const hash = (location.hash || "#wall").slice(1);
  const start = nav.querySelector(`[data-screen="${hash}"]`) || nav.querySelector(".sn");
  if (start && !start.classList.contains("on")) start.click();

  /* mast */
  $("mast").innerHTML = `
    <div>
      <div class="kicker">Maryland Terrapins · Big Ten · Fear the Turtle</div>
      <h1 class="cond"><span class="t">Terps</span> Football Wall</h1>
      <div class="sub">Season ${D.season} · ESPN data pulled ${fmtTime(D.fetched_at)} · ${D.source_count} cached responses · remaster Sat Oct 10 afternoon</div>
    </div>
    <div class="rec-row" id="bigrec"></div>`;
  $("bigrec").innerHTML = `
    <div class="pill"><b class="cond">${esc(cr.total)}</b><span>Overall</span></div>
    <div class="pill r"><b class="cond">${esc(cr.vsconf)}</b><span>Big Ten</span></div>
    <div class="pill"><b class="cond">${md.seed}<small style="font-size:16px">/18</small></b><span>B1G ESPN order</span></div>
    <div class="pill r"><b class="cond">${B.wins_needed}</b><span>Wins to bowl</span></div>`;

  /* ticker */
  const tk =
    G.map((g) =>
      g.final
        ? `<span><span class="${g.win ? "w" : "l"}">${g.result}</span> ${g.home ? "vs" : "@"} ${esc(g.opp.abbr)} ${g.md_score}-${g.opp_score}</span>`
        : `<span><span class="g">${esc(g.date_et)}</span> ${g.home ? "vs" : "@"} ${g.opp.rank ? "#" + g.opp.rank + " " : ""}${esc(g.opp.abbr)} · ${esc(g.time_valid ? g.time_et : "TBA")} ${esc(g.tv.join("/"))}</span>`
    ).join("") + `<span class="g">★ Fear the Turtle ★</span>`;
  $("ticker").innerHTML = tk + tk;

  /* wall hero */
  $("hero").innerHTML = `
    <div class="kicker" style="color:var(--gold);letter-spacing:.18em;font-size:11px;margin-bottom:6px">2026 SEASON WALL</div>
    <h2 class="cond" style="font-size:34px;margin:0 0 8px">Fear the Turtle</h2>
    <p class="lede" style="margin-bottom:14px">Multi-screen tracker for Boyd. Scores and records are ESPN-only from on-disk cache — never invented. Kickoffs shown in Eastern.</p>
    <div class="rec-row">
      <div class="pill"><b class="cond">${done.length}</b><span>Played</span></div>
      <div class="pill r"><b class="cond">${left.length}</b><span>Left</span></div>
      <div class="pill"><b class="cond">${md.streak || "—"}</b><span>Streak</span></div>
      <div class="pill r"><b class="cond">${md.diff > 0 ? "+" : ""}${md.diff}</b><span>Point diff</span></div>
    </div>`;

  /* next game */
  const nx = left[0];
  if (nx) {
    const o = nx.opp;
    const md1 = `<div class="tm"><div class="ab cond">MD</div><div class="rec cond">${esc(cr.total)}</div><div class="nm">Maryland</div></div>`;
    const op1 = `<div class="tm"><div class="ab cond">${o.rank ? `<small style="font-size:20px;color:var(--gold)">#${o.rank}</small> ` : ""}${esc(o.abbr)}</div><div class="rec cond">${esc(o.overall || "")}</div><div class="nm">${esc(o.location)}</div></div>`;
    $("next").innerHTML = `<div class="next">
      <div class="bar cond"><span>Next up · Week ${nx.week}</span><span class="live">${esc(nx.date_et)} · ${esc(nx.time_et)}</span></div>
      <div class="matchup">${nx.home ? op1 : md1}<div class="at cond">${nx.home ? "vs" : "@"}</div>${nx.home ? md1 : op1}</div>
      <div class="nmeta">
        <div><small>TV</small><b class="cond">${esc(nx.tv.join(", ") || "TBA")}</b></div>
        <div><small>Line${nx.line ? " (" + esc(nx.line.provider) + ")" : ""}</small><b class="cond">${nx.line ? esc(nx.line.details) + ` <span style="font-size:12px;color:var(--mut)">O/U ${esc(nx.line.ou)}</span>` : "—"}</b></div>
        <div><small>ESPN predictor · MD win</small><b class="cond">${nx.espn_md_win_pct != null ? nx.espn_md_win_pct + "%" : "—"}</b></div>
      </div>
      <div class="venue">${esc(nx.venue)}${nx.city ? " · " + esc(nx.city) : ""}</div>
    </div>`;
  } else {
    $("next").innerHTML = `<div class="next" style="padding:24px"><p class="lede">No remaining games in cached schedule.</p></div>`;
  }

  /* form strip */
  $("form-strip").innerHTML =
    `<h2 class="cond" style="font-size:22px">Season strip</h2><div class="form-row">` +
    G.map((g) => {
      if (g.final) {
        return `<div class="gm ${g.result}"><div class="w">Wk ${g.week}</div><div class="o">${g.home ? "vs" : "@"} ${esc(g.opp.abbr)}</div><div class="r">${g.result} ${g.md_score}-${g.opp_score}</div></div>`;
      }
      return `<div class="gm fut"><div class="w">Wk ${g.week}</div><div class="o">${g.home ? "vs" : "@"} ${esc(g.opp.abbr)}</div><div class="r">${esc(g.time_valid ? g.time_et.replace(" ET", "") : "TBA")}</div></div>`;
    }).join("") +
    `</div>`;

  /* bowl chip on wall */
  const meter = Array.from({ length: 6 }, (_, i) =>
    i < B.countable_wins ? `<i class="cond won">${i + 1}</i>` : `<i class="cond need">${i + 1}</i>`
  ).join("");
  $("bowl-chip").innerHTML = `
    <h2 class="cond" style="font-size:22px">Bowl meter</h2>
    <div style="display:flex;align-items:flex-end;gap:12px"><div class="bignum cond">${B.wins_needed}</div>
    <div class="cond" style="font-size:18px;line-height:1.1">more wins needed<br><span style="color:var(--mut);font-size:13px;font-family:SG;font-weight:400;text-transform:none;letter-spacing:0">in ${B.games_left} left · can lose ${B.can_lose}</span></div></div>
    <div class="meter">${meter}</div>
    <div class="note">Countable wins ${B.countable_wins}/6 · P(bowl) <b style="color:var(--gold)">${B.p_bowl_espn_based}%</b> <span class="est">Estimate</span></div>`;

  /* wall notes teaser */
  const bullets = (N.bullets || []).slice(0, 4);
  $("wall-notes").innerHTML =
    `<h2 class="cond" style="font-size:22px">Season notes</h2><p class="lede">${esc(N.disclaimer || "")}</p><ul class="notes-list">` +
    bullets
      .map((b) => {
        const cls = b.tag === "Estimate" ? "esttag" : b.tag === "Data quirk" ? "quirk" : "";
        return `<li><span class="ntag ${cls}">${esc(b.tag)}</span><span>${esc(b.text)}</span></li>`;
      })
      .join("") +
    `</ul><p class="note">Open the <button type="button" class="sn" style="display:inline;padding:4px 10px;margin:0 4px" id="goto-notes">Season Notes</button> screen for full quirks &amp; sources.</p>`;
  const gn = $("goto-notes");
  if (gn) gn.addEventListener("click", () => nav.querySelector('[data-screen="notes"]').click());

  /* results */
  const pf = done.reduce((a, g) => a + g.md_score, 0),
    pa = done.reduce((a, g) => a + g.opp_score, 0);
  let sk = 0;
  for (let i = done.length - 1; i >= 0 && done[i].win === done[done.length - 1].win; i--) sk++;
  $("reslede").textContent = `${done.length} games played: ${pf} points scored, ${pa} allowed. Current streak: ${sk} straight ${done[done.length - 1].win ? "win" : "loss"}${sk > 1 ? (done[done.length - 1].win ? "s" : "es") : ""}.`;
  const lineTxt = (g) => {
    const k = Object.keys(g.linescores);
    return k.map((t) => `${t.padEnd(5, " ")} ${g.linescores[t].join("  ")}`).join(" · ");
  };
  $("games").innerHTML = done
    .map((g) => {
      const o = g.opp;
      const mdS = `<div class="n cond ${g.win ? "win" : "lose"}">Maryland</div><div class="s cond ${g.win ? "win" : "lose"}">${g.md_score}</div>`;
      const opS = `<div class="n cond ${g.win ? "lose" : "win"}">${esc(o.location)}${g.fcs ? ' <span class="tag">FCS</span>' : ""}</div><div class="s cond ${g.win ? "lose" : "win"}">${g.opp_score}</div>`;
      const rows = ["Total Yards", "Passing", "Rushing", "1st Downs", "3rd down efficiency", "Turnovers", "Penalties", "Possession"]
        .map((k) => {
          const a = g.box.md[k],
            b = g.box.opp[k];
          const better =
            k === "Turnovers" ? +a < +b : k === "Penalties" || k.includes("efficiency") || k === "Possession" ? null : +a > +b;
          return `<tr><td>${k}</td><td class="${better ? "b" : ""}">${esc(a)}</td><td>${esc(b)}</td></tr>`;
        })
        .join("");
      const t = g.md_top,
        pp = [];
      if (t.passing)
        pp.push(
          `<div><small>Passing</small>${esc(t.passing.name)}<br>${esc(t.passing.line["C/ATT"])}, ${esc(t.passing.line.YDS)} yds, ${esc(t.passing.line.TD)} TD, ${esc(t.passing.line.INT)} INT</div>`
        );
      if (t.rushing)
        pp.push(
          `<div><small>Rushing</small>${esc(t.rushing.name)}<br>${esc(t.rushing.line.CAR)} car, ${esc(t.rushing.line.YDS)} yds, ${esc(t.rushing.line.TD)} TD</div>`
        );
      if (t.receiving)
        pp.push(
          `<div><small>Receiving</small>${esc(t.receiving.name)}<br>${esc(t.receiving.line.REC)} rec, ${esc(t.receiving.line.YDS)} yds, ${esc(t.receiving.line.TD)} TD</div>`
        );
      if (t.defensive)
        pp.push(
          `<div><small>Tackles</small>${esc(t.defensive.name)}<br>${esc(t.defensive.line.TOT)} tkl, ${esc(t.defensive.line.SACKS)} sk, ${esc(t.defensive.line.TFL)} TFL</div>`
        );
      return `<div class="g"><div class="top cond"><span>Wk ${g.week} · ${esc(g.date_et)} · ${g.home ? "Home" : "Away"}${g.conference ? ' · <span style="color:var(--gold)">B1G</span>' : ""}</span><span class="badge ${g.result}">${g.result} ${g.md_score}-${g.opp_score}</span></div>
        <div class="score">${g.home ? opS + mdS : mdS + opS}</div><div class="lines">Q1–Q4 · ${esc(lineTxt(g))}</div>
        ${g.headline ? `<div class="hl">“${esc(g.headline)}”<span style="font-style:normal;color:var(--mut)"> (ESPN recap headline)</span></div>` : ""}
        <table class="bx"><tr><td style="color:var(--mut)">Team stats</td><td class="cond" style="color:var(--gold)">MD</td><td class="cond">${esc(o.abbr)}</td></tr>${rows}</table>
        <div class="perf">${pp.join("")}</div><div style="padding:0 12px 10px;font-size:11.5px;color:var(--mut)">${esc(g.venue)} · ${esc(g.tv.join(", "))}</div></div>`;
    })
    .join("");

  /* bowl screen */
  const byId = Object.fromEntries(G.map((g) => [g.id, g]));
  const wl = B.winnable_order
    .map((id, i) => {
      const g = byId[id],
        o = g.opp;
      return `<div class="wrow"><div class="rk cond">${i + 1}</div><div><div class="o cond">${g.home ? "vs" : "@"} ${o.rank ? "#" + o.rank + " " : ""}${esc(o.location)}<small>${esc(o.overall)} (${esc(o.conf)} B1G) · ${esc(g.date_et)}</small></div>
      <div class="bars"><div class="bb"><b style="width:${g.espn_md_win_pct}%"></b></div><div class="bb m"><b style="width:${g.record_model_win_pct}%"></b></div></div></div>
      <div class="pct cond">${g.espn_md_win_pct}%<small>ESPN predictor<br>my est. ${g.record_model_win_pct}%</small></div></div>`;
    })
    .join("");
  const mx = Math.max(...B.win_distribution.map((d) => d.pct), 1);
  $("bowlbox").innerHTML = `<div class="panel"><div class="cond" style="font-size:16px;color:var(--mut)">Countable wins</div>
    <div style="display:flex;align-items:flex-end;gap:16px"><div class="bignum cond">${B.wins_needed}</div><div class="cond" style="font-size:20px;line-height:1.05">more wins needed<br><span style="color:var(--mut);font-size:14px;font-family:SG;font-weight:400;text-transform:none;letter-spacing:0">in ${B.games_left} games left</span></div></div>
    <div class="meter">${meter}</div>
    <div style="font-size:14px">Maryland needs <b>${B.wins_needed} of its last ${B.games_left}</b>, so it can afford <b>${B.can_lose}</b> more losses. Best possible finish: <b>${B.max_wins}-${12 - B.max_wins}</b>.</div>
    <div class="note">${(() => {
      const f = G.filter((g) => g.fcs);
      return f.length
        ? `FCS games on the schedule: ${f.map((g) => esc(g.opp.location) + " (" + (g.final ? g.result + " " + g.md_score + "-" + g.opp_score : "upcoming") + ")").join(", ")}. ${B.fcs_wins <= 1 ? "There's only one FCS win, so it counts toward the six." : `Only one of the ${B.fcs_wins} FCS wins counts.`}`
        : "There are no FCS opponents on the schedule.";
    })()}</div>
    <div style="margin-top:18px" class="cond">Final regular-season wins <span class="est">Estimate</span></div>
    <div class="hist">${B.win_distribution.map((d) => `<div class="${d.final_wins >= 6 ? "ok" : ""}" style="height:${Math.max(1, (d.pct / mx) * 100)}%"><span>${d.pct}%</span></div>`).join("")}</div>
    <div class="hlab cond">${B.win_distribution.map((d) => `<div>${d.final_wins}</div>`).join("")}</div>
    <div style="margin-top:12px;font-size:14px">Chance of reaching 6 wins: <b class="cond" style="font-size:26px;color:var(--gold)">${B.p_bowl_espn_based}%</b> <span class="est">Estimate</span> · expected finish ≈ <b>${B.expected_final_wins}</b> wins</div>
    <div class="note">Exact win-count over remaining games using ESPN Matchup Predictor %, treating games as independent. TokenMax math on ESPN projections — not an official ESPN figure.</div></div>
    <div class="panel"><div class="cond" style="font-size:20px">Most winnable remaining games</div>
    <div class="note" style="margin:2px 0 8px">Ranked by ESPN Matchup Predictor (<span style="color:var(--gold)">red-gold bar</span>). Grey bar = record-based estimate (smoothed W%, ±5 home/away). <span class="est">Estimate</span></div>${wl}</div>`;

  /* standings */
  const leftIds = new Set(left.map((g) => g.opp.id)),
    playedIds = new Set(done.map((g) => g.opp.id));
  $("stand").innerHTML =
    `<tr><th>#</th><th>Team</th><th>B1G</th><th>Overall</th><th class="hide-m">Home</th><th class="hide-m">Away</th><th class="r hide-m">PF</th><th class="r hide-m">PA</th><th class="r">Diff</th><th>Strk</th></tr>` +
    D.standings
      .map(
        (s) =>
          `<tr class="${s.id === "120" ? "md" : leftIds.has(s.id) ? "opp" : ""}"><td>${s.seed}</td><td>${s.rank ? `<b style="color:var(--gold)">#${s.rank}</b> ` : ""}${esc(s.location)}${leftIds.has(s.id) ? '<span class="tag">Left</span>' : ""}${playedIds.has(s.id) ? '<span class="tag" style="color:#a1a1aa;border-color:#444">Played</span>' : ""}</td><td><b>${esc(s.conf)}</b></td><td>${esc(s.overall)}</td><td class="hide-m">${esc(s.home)}</td><td class="hide-m">${esc(s.away)}</td><td class="r hide-m">${s.pf}</td><td class="r hide-m">${s.pa}</td><td class="r" style="color:${s.diff > 0 ? "var(--grn)" : s.diff < 0 ? "#f87171" : "inherit"}">${s.diff > 0 ? "+" : ""}${s.diff}</td><td>${esc(s.streak)}</td></tr>`
      )
      .join("");

  /* schedule */
  $("sched").innerHTML =
    `<tr><th>Wk</th><th>Date</th><th>Opponent</th><th>Opp. record</th><th>Kickoff (ET)</th><th>TV</th><th class="hide-m">Venue</th><th class="r">ESPN MD win</th></tr>` +
    left
      .map(
        (g) =>
          `<tr><td>${g.week}</td><td>${esc(g.date_et)}</td><td><b>${g.home ? "vs" : "@"} ${g.opp.rank ? '<span style="color:var(--gold)">#' + g.opp.rank + "</span> " : ""}${esc(g.opp.location)}</b></td><td>${esc(g.opp.overall)} <span style="color:var(--mut)">(${esc(g.opp.conf)})</span></td><td>${g.time_valid ? esc(g.time_et) : '<span style="color:var(--mut)">TBA</span>'}</td><td>${g.tv.length ? esc(g.tv.join(", ")) : '<span style="color:var(--mut)">TBA</span>'}</td><td class="hide-m">${esc(g.venue)}</td><td class="r cond" style="font-size:18px">${g.espn_md_win_pct}%</td></tr>`
      )
      .join("") +
    (() => {
      const wk = new Set(G.map((g) => g.week)),
        mxw = Math.max(...wk),
        miss = [];
      if (!left.length) return "";
      for (let w = Math.min(...left.map((g) => g.week)); w <= mxw; w++) if (!wk.has(w)) miss.push(w);
      return miss.length
        ? `<tr><td colspan="8" style="color:var(--mut);font-size:12.5px">Open date${miss.length > 1 ? "s" : ""}: week ${miss.join(", ")}. ESPN lists no game for Maryland.</td></tr>`
        : "";
    })();

  /* leaders */
  $("lead").innerHTML = D.leaders
    .map((l) => {
      const f = l.top[0];
      return `<div class="ld"><h3 class="cond">${esc(l.label)}</h3><div class="first"><div class="jn cond">${esc(f.jersey || "")}</div><div><div class="nm">${esc(f.name)}</div><div class="meta">${esc(f.pos || "")} · ${esc(f.class || "")}${f.line ? "<br>" + esc(f.line) : ""}</div></div><div class="v cond">${esc(f.value)}</div></div><ol start="2">${l.top
        .slice(1)
        .map((t) => `<li>${esc(t.name)} <span style="color:var(--mut)">${esc(t.pos || "")}</span><b>${esc(t.value)}</b></li>`)
        .join("")}</ol></div>`;
    })
    .join("");
  {
    const mm = [];
    D.leaders.forEach((l) =>
      l.top.forEach((t) => {
        if (t.box_mismatch)
          mm.push(
            `${esc(t.name)} (${esc(l.label.toLowerCase())}): ESPN season feed ${esc(t.value)}, box scores sum ${t.box_sum}`
          );
      })
    );
    if (mm.length)
      $("lead").insertAdjacentHTML(
        "afterend",
        `<div class="note">Where ESPN feeds disagree: ${mm.join("; ")}. Cards show the season-feed number. Passing, rushing and receiving yards match exactly.</div>`
      );
  }
  const ts = D.team_stats,
    cmpRows = [
      ["Points", "ppg"],
      ["Total yds", "ypg"],
      ["Pass yds", "pass_ypg"],
      ["Rush yds", "rush_ypg"],
      ["Yds/carry", "ypc"],
      ["3rd down %", "third_pct"],
      ["Sacks", "sacks"],
      ["Takeaways", "takeaways"],
    ];
  $("cmp").innerHTML =
    `<div class="crow"><div class="cond" style="color:var(--gold)">Terps</div><div class="lab">per game unless noted</div><div class="b cond">Opponents</div></div><div class="crow hide-m"></div>` +
    cmpRows
      .map(
        ([l, k]) =>
          `<div class="crow"><div class="a">${esc(ts.md[k])}</div><div class="lab">${l}${["sacks", "takeaways"].includes(k) ? " (season)" : ""}</div><div class="b">${esc(ts.opp[k])}</div></div>`
      )
      .join("");

  /* season notes screen */
  $("notes-root").innerHTML =
    `<h2 class="cond">Season Notes</h2><p class="lede">${esc(N.disclaimer || "")}</p><p class="note">${esc(N.remaster || "")} · ${esc(N.sources_note || "")}</p><ul class="notes-list">` +
    (N.bullets || [])
      .map((b) => {
        const cls = b.tag === "Estimate" ? "esttag" : b.tag === "Data quirk" ? "quirk" : "";
        return `<li><span class="ntag ${cls}">${esc(b.tag)}</span><span>${esc(b.text)}</span></li>`;
      })
      .join("") +
    `</ul>`;

  $("src").innerHTML = `<div class="cond" style="font-size:18px;color:var(--ink)">Sources &amp; methods</div>
    <p>All numbers come from ESPN's public site and core APIs. The ${D.source_count} raw responses are cached with URLs and fetch times in <code>data/raw</code> and <code>data/manifest.json</code>. Pulled ${fmtTime(D.fetched_at)}. Kickoffs converted to Eastern. Anything labeled <span class="est">Estimate</span> is a model, not a fact.</p>
    <ul>${D.sources.map((s) => `<li>${esc(s.name)}: <a href="${esc(s.url)}">${esc(s.url)}</a></li>`).join("")}<li>Per-game box scores, recaps and Matchup Predictor: <code>…/college-football/summary?event=&lt;id&gt;</code>.</li></ul>
    <p>Built by TokenMax for Boyd (UMD) · Go Terps · Sat Oct 10 afternoon remaster.</p>`;

  document.body.dataset.ready = "1";
  } // end boot

  if (window.__TRACKER__) {
    boot(window.__TRACKER__, window.__NOTES__ || null);
  } else {
    Promise.all([
      fetch("/api/data").then((r) => (r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status)))),
      fetch("/api/notes").then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ]).then(([t, n]) => boot(t, n)).catch((e) => fail(e.message));
  }
})();
