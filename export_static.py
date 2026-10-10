#!/usr/bin/env python3
"""Write dist/terps-football-snapshot.html (+ legacy alias): one offline file with CSS/JS/fonts/data inlined."""
import base64, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "web")


def main():
    rd = lambda n: open(os.path.join(W, n), encoding="utf-8").read()
    html, css, js = rd("index.html"), rd("style.css"), rd("app.js")
    css = re.sub(
        r'url\("(fonts/[^"]+)"\)',
        lambda m: 'url("data:font/ttf;base64,' + base64.b64encode(open(os.path.join(W, m.group(1)), "rb").read()).decode() + '")',
        css,
    )
    data = json.load(open(os.path.join(HERE, "data", "tracker.json"), encoding="utf-8"))
    notes = {}
    np = os.path.join(HERE, "data", "season_notes.json")
    if os.path.exists(np):
        notes = json.load(open(np, encoding="utf-8"))
    html = html.replace('<link rel="stylesheet" href="style.css">', "<style>\n" + css + "\n</style>")
    html = html.replace("<!--TRACKERDATA-->", "<script>window.__TRACKER__=" + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + ";</script>")
    html = html.replace("<!--NOTESDATA-->", "<script>window.__NOTES__=" + json.dumps(notes, ensure_ascii=False).replace("</", "<\\/") + ";</script>")
    html = html.replace('<script src="app.js"></script>', "<script>\n" + js.replace("</script", "<\\/script") + "\n</script>")
    os.makedirs(os.path.join(HERE, "dist"), exist_ok=True)
    for name in ("terps-football-snapshot.html", "terps-football-2026.html", "index.html"):
        out = os.path.join(HERE, "dist", name)
        open(out, "w", encoding="utf-8").write(html)
    print(f"dist/terps-football-snapshot.html ({os.path.getsize(os.path.join(HERE, 'dist', 'terps-football-snapshot.html'))//1024} KB)")


if __name__ == "__main__":
    main()
