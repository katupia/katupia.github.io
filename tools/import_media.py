"""Copy media files into a gallery section, optionally taking captions from a PZ translation file.

  python tools/import_media.py pz/TooManyEmotes/media/loops SRC.avif [SRC ...]
      [--captions UI.json --key-prefix UI_TME_Emote_] [--force]

Existing files are kept unless --force (published URLs must not change content silently).
Captions are merged into <section>/captions.json; a file matches the key whose suffix
has the same letters and digits as its name ("APT." -> APT.avif, "bye-bye-bye" -> bye_bye_bye.avif).
Run tools/build.py afterwards.
"""
import argparse, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("section", help="destination folder, relative to the site root")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--captions", help="JSON file of key -> text")
    ap.add_argument("--key-prefix", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    dest = os.path.join(ROOT, a.section)
    os.makedirs(dest, exist_ok=True)
    texts = {}
    if a.captions:
        with open(a.captions, encoding="utf-8") as f:
            texts = json.load(f)
    # file names are sanitized entry names ("APT.", "bobbin'", "boy's_a_liar", "bye-bye-bye"):
    # compare letters and digits only
    def norm(t):
        return re.sub(r"[^a-z0-9]", "", t.casefold())

    by_stem = {}
    for key, text in texts.items():
        if key.startswith(a.key_prefix):
            by_stem.setdefault(norm(key[len(a.key_prefix):]), text)
    cap_path = os.path.join(dest, "captions.json")
    caps = {}
    if os.path.isfile(cap_path):
        with open(cap_path, encoding="utf-8") as f:
            caps = json.load(f)

    for src in a.files:
        name = os.path.basename(src)
        out = os.path.join(dest, name)
        if os.path.exists(out) and not a.force:
            print(f"kept   {name} (exists)")
        else:
            shutil.copy2(src, out)
            print(f"copied {name} ({os.path.getsize(out) // 1024} kB)")
        stem = os.path.splitext(name)[0]
        if norm(stem) in by_stem:
            caps[name] = by_stem[norm(stem)]

    if caps:
        with open(cap_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(dict(sorted(caps.items(), key=lambda kv: kv[0].casefold())), f, indent=2, ensure_ascii=False)
            f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
