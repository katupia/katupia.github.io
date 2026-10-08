"""Copy media files into a gallery section, optionally taking captions from a PZ translation file.

  python tools/import_media.py pz/TooManyEmotes/media/loops SRC.avif [SRC ...]
      [--captions UI.json --key-prefix UI_TME_Emote_] [--force]

Existing files are kept unless --force (published URLs must not change content silently).
Captions are merged into <section>/captions.json; for a file "APT.avif" the keys tried are
<prefix>APT then <prefix>APT. (entry names may end with a dot that is not in the file name).
Run tools/build.py afterwards.
"""
import argparse, json, os, shutil, sys

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
        for key in (a.key_prefix + stem, a.key_prefix + stem + "."):
            if key in texts:
                caps[name] = texts[key]
                break

    if caps:
        with open(cap_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(dict(sorted(caps.items(), key=lambda kv: kv[0].casefold())), f, indent=2, ensure_ascii=False)
            f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
