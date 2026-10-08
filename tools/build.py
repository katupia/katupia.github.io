"""Generate the static pages of katupia.github.io from site.json and the media on disk.

  python tools/build.py

Layout (URLs are stable: Workshop descriptions link to them):
  <game>/<Mod>/poster.png|jpg|webp|avif   optional, card image on the listings
  <game>/<Mod>/media/<section>/<file>     gallery images, one gallery section per folder
  <game>/<Mod>/media/<section>/captions.json   optional {"file.avif": "Caption"}

Captions default to the file name (underscores -> spaces, first letter of each word
upper-cased unless the word already has capitals). Section titles and notes come from
site.json ("sections"), otherwise from the folder name.

Generated: index.html, <game>/index.html, <game>/<Mod>/index.html, <game>/<Mod>/media.json
(absolute URLs of every media file, for scripts and Workshop descriptions).
"""
import html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_EXT = (".avif", ".webp", ".png", ".jpg", ".jpeg", ".gif")
POSTER_NAMES = [f"poster{e}" for e in IMAGE_EXT]

e = html.escape


def caption_from_name(stem):
    words = stem.replace("_", " ").split()
    return " ".join(w if any(c.isupper() for c in w) else w[:1].upper() + w[1:] for w in words)


def sort_key(name):
    return name.casefold()


def find_poster(mod_dir):
    for p in POSTER_NAMES:
        if os.path.isfile(os.path.join(mod_dir, p)):
            return p
    return None


def scan_sections(mod_dir, mod):
    media_dir = os.path.join(mod_dir, "media")
    if not os.path.isdir(media_dir):
        return []
    meta = mod.get("sections", {})
    order = list(meta)
    folders = sorted((d for d in os.listdir(media_dir) if os.path.isdir(os.path.join(media_dir, d))),
                     key=lambda d: (order.index(d) if d in order else len(order), sort_key(d)))
    sections = []
    for d in folders:
        folder = os.path.join(media_dir, d)
        caps = {}
        cap_file = os.path.join(folder, "captions.json")
        if os.path.isfile(cap_file):
            with open(cap_file, encoding="utf-8") as f:
                caps = json.load(f)
        items = []
        for name in sorted(os.listdir(folder), key=sort_key):
            if name.lower().endswith(IMAGE_EXT):
                stem = os.path.splitext(name)[0]
                items.append({"file": f"media/{d}/{name}",
                              "caption": caps.get(name, caption_from_name(stem)),
                              "bytes": os.path.getsize(os.path.join(folder, name))})
        if items:
            m = meta.get(d, {})
            sections.append({"id": d, "title": m.get("title", caption_from_name(d)),
                             "note": m.get("note", ""), "items": items})
    return sections


def page(site, title, depth, crumbs, body, description=""):
    up = "../" * depth
    nav = '<span aria-hidden="true">/</span>'.join(f'<a href="{up}{href}">{e(label)}</a>'
                                                   for label, href in crumbs)
    full_title = f"{title} · {site['title']}" if depth else site["title"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description or site['tagline'])}">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
<header class="top">
  <nav class="crumbs"><a class="brand" href="{up}">{e(site['title'])}</a>{'<span aria-hidden="true">/</span>' if crumbs else ''}{nav}</nav>
</header>
<main>
{body}
</main>
<footer class="foot">{e(site['author'])} · mods for Project Zomboid and Outward</footer>
<script src="{up}assets/site.js" defer></script>
</body>
</html>
"""


def mod_card(game, mod, prefix):
    mod_dir = os.path.join(ROOT, game["id"], mod["id"])
    poster = find_poster(mod_dir)
    img = (f'<img src="{prefix}{mod["id"]}/{poster}" alt="" width="96" height="96" loading="lazy">'
           if poster else '<div class="ph" aria-hidden="true"></div>')
    status = f'<span class="tag">{e(mod["status"])}</span>' if mod.get("status") else ""
    return f"""<a class="card" href="{prefix}{mod['id']}/">
  {img}
  <div><h3>{e(mod['name'])} {status}</h3><p>{e(mod.get('summary', ''))}</p></div>
</a>"""


def mod_list(game, prefix):
    if not game["mods"]:
        return '<p class="empty">Nothing here yet.</p>'
    return '<div class="cards">' + "\n".join(mod_card(game, m, prefix) for m in game["mods"]) + "</div>"


def build_home(site):
    parts = [f'<section class="hero"><h1>{e(site["title"])}</h1><p>{e(site["tagline"])}</p></section>']
    for g in site["games"]:
        parts.append(f"""<section class="game">
<h2><a href="{g['id']}/">{e(g['name'])}</a></h2>
{mod_list(g, g['id'] + '/')}
</section>""")
    return page(site, site["title"], 0, [], "\n".join(parts))


def build_game(site, g):
    body = f"""<section class="hero"><h1>{e(g['name'])}</h1><p>{e(g.get('summary', ''))}</p></section>
<section class="game">{mod_list(g, '')}</section>"""
    return page(site, g["name"], 1, [(g["name"], g["id"] + "/")], body, g.get("summary", ""))


def build_mod(site, g, mod):
    mod_dir = os.path.join(ROOT, g["id"], mod["id"])
    base = f"{site['baseUrl']}/{g['id']}/{mod['id']}/"
    sections = scan_sections(mod_dir, mod)
    poster = find_poster(mod_dir)

    head = [f'<section class="hero mod">']
    if poster:
        head.append(f'<img class="poster" src="{poster}" alt="" width="128" height="128">')
    head.append("<div>")
    head.append(f"<h1>{e(mod['name'])}</h1>")
    if mod.get("status"):
        head.append(f'<span class="tag">{e(mod["status"])}</span>')
    if mod.get("summary"):
        head.append(f'<p class="lead">{e(mod["summary"])}</p>')
    links = mod.get("links", [])
    if links:
        head.append('<p class="links">' + " ".join(
            f'<a class="btn" href="{e(l["url"])}">{e(l["label"])}</a>' for l in links) + "</p>")
    head.append("</div></section>")

    prose = "".join(f"<p>{e(p)}</p>" for p in mod.get("description", []))
    if mod.get("credits"):
        prose += f'<p class="credits">{e(mod["credits"])}</p>'
    body = ["\n".join(head)]
    if prose:
        body.append(f'<section class="prose">{prose}</section>')

    manifest = {"mod": mod["id"], "game": g["id"], "page": base, "sections": {}}
    for s in sections:
        figs = []
        for it in s["items"]:
            url = base + it["file"]
            figs.append(f"""<figure class="tile">
  <img src="{e(it['file'])}" alt="{e(it['caption'])}" width="256" height="256" loading="lazy">
  <figcaption><span>{e(it['caption'])}</span><button type="button" class="copy" data-url="{e(url)}" title="Copy the image URL">URL</button></figcaption>
</figure>""")
        manifest["sections"][s["id"]] = [{"url": base + it["file"], "caption": it["caption"], "bytes": it["bytes"]}
                                         for it in s["items"]]
        note = f'<p class="note">{e(s["note"])}</p>' if s["note"] else ""
        body.append(f"""<section class="gallery" id="{e(s['id'])}">
<h2>{e(s['title'])} <span class="count">{len(s['items'])}</span></h2>
{note}
<div class="grid">
{chr(10).join(figs)}
</div>
</section>""")

    crumbs = [(g["name"], g["id"] + "/"), (mod["name"], f"{g['id']}/{mod['id']}/")]
    return page(site, mod["name"], 2, crumbs, "\n".join(body), mod.get("summary", "")), manifest


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    with open(os.path.join(ROOT, "site.json"), encoding="utf-8") as f:
        site = json.load(f)
    write(os.path.join(ROOT, "index.html"), build_home(site))
    for g in site["games"]:
        write(os.path.join(ROOT, g["id"], "index.html"), build_game(site, g))
        for mod in g["mods"]:
            text, manifest = build_mod(site, g, mod)
            write(os.path.join(ROOT, g["id"], mod["id"], "index.html"), text)
            write(os.path.join(ROOT, g["id"], mod["id"], "media.json"),
                  json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
            n = sum(len(v) for v in manifest["sections"].values())
            print(f"{g['id']}/{mod['id']}: {n} media")
    return 0


if __name__ == "__main__":
    sys.exit(main())
