# katupia.github.io

External pages and media for Tchernobill's Project Zomboid and Outward mods,
served by GitHub Pages at https://katupia.github.io/.

Plain static files, no Jekyll (`.nojekyll`). The HTML pages are generated:

```
python tools/build.py
```

## Layout

```
site.json                          games, mods, texts, gallery section titles
assets/style.css, assets/site.js   shared style and the "copy URL" buttons
<game>/<Mod>/poster.png            card image (optional)
<game>/<Mod>/media/<section>/*     gallery images, one section per folder
<game>/<Mod>/media/<section>/captions.json   optional {"file.avif": "Caption"}
```

Generated (commit them): `index.html`, `<game>/index.html`,
`<game>/<Mod>/index.html`, `<game>/<Mod>/media.json` (absolute URLs of the media).

Media URLs are linked from Workshop descriptions: never rename or move a published file.

## Adding things

- A mod: add an entry under its game in `site.json` (`id` = folder name), run the build.
- Images: drop them in `<game>/<Mod>/media/<section>/`, run the build, commit, push.
