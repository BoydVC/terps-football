// Screenshots of the offline snapshot via CDP (desktop + phone, section crops). Also fails on any JS error.
import { launch } from "./cdp.mjs";
import { writeFileSync } from "node:fs";
const dir = new URL("..", import.meta.url).pathname;
const url = "file://" + dir + "dist/terps-football-2026.html";
const b = await launch(9572, 1440, 1000);
const clipShot = async (path, sel, scale = 1) => {
  const r = await b.ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect();return {x:0,y:e.top+scrollY-14,w:document.documentElement.clientWidth,h:e.height+28}})()`);
  const s = await b.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: r.x, y: Math.max(0, r.y), width: r.w, height: r.h, scale } });
  writeFileSync(dir + path, Buffer.from(s.data, "base64")); console.log("  " + path);
};
await b.viewport(1440, 1000); await b.goto(url, 2000);
await b.ev(`document.querySelector('.ticker .in').style.animation='none'`);
await b.shot(dir + "screenshots/00-best-desktop-hero.png"); console.log("  screenshots/00-best-desktop-hero.png");
await clipShot("screenshots/02-desktop-results.png", "#results");
await clipShot("screenshots/03-desktop-bowl-watch.png", "#bowl");
await clipShot("screenshots/04-desktop-standings.png", "#standings");
await clipShot("screenshots/05-desktop-schedule.png", "#schedule");
await clipShot("screenshots/05b-desktop-leaders.png", "#leaders");
await clipShot("screenshots/01-desktop-full.png", "body", 0.6);
await b.viewport(390, 844, true, 2); await b.goto(url, 2000);
await b.ev(`document.querySelector('.ticker .in').style.animation='none'`);
await b.shot(dir + "screenshots/06-phone-hero.png"); console.log("  screenshots/06-phone-hero.png");
await clipShot("screenshots/07-phone-bowl-watch.png", "#bowl", 2);
await clipShot("screenshots/08-phone-standings.png", "#standings", 2);
const errs = b.errors.slice(); await b.close();
if (errs.length) { console.error("JS errors:", errs); process.exit(1); }
console.log("no JS errors");
