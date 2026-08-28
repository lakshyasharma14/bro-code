#!/usr/bin/env python3
"""Replace ```mermaid fences in an .mdx file with rendered PNG embeds.

This blog's MDX pipeline has no mermaid renderer, so a ```mermaid fence
just prints as a plain-text code block. This script renders each such
fence via the public mermaid.ink API and rewrites the fence as
<center>![alt](/static/images/<slug>/diagram-N.png)</center>, matching
this repo's existing image-embed convention.

Usage:
    python3 render_mermaid.py <path/to/post.mdx> [--width 1600] [--bg white]

Diagrams are saved to public/static/images/<post-slug>/diagram-N.png,
where <post-slug> is the .mdx filename without extension. The .mdx file
is edited in place; a .bak backup is written alongside it.
"""
import argparse
import base64
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FENCE_RE = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)


def render_png(mermaid_src: str, width: int, bg: str) -> bytes:
    encoded = base64.urlsafe_b64encode(mermaid_src.encode()).decode()
    params = urllib.parse.urlencode({"type": "png", "backgroundColor": bg, "width": width})
    url = f"https://mermaid.ink/img/{encoded}?{params}"
    # mermaid.ink sits behind Cloudflare, which 403s Python's default User-Agent.
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"mermaid.ink returned HTTP {resp.status} for a diagram")
        return resp.read()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mdx_path", type=Path)
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--bg", default="white")
    args = ap.parse_args()

    mdx_path = args.mdx_path.resolve()
    if not mdx_path.is_file():
        sys.exit(f"error: {mdx_path} not found")

    text = mdx_path.read_text()
    matches = list(FENCE_RE.finditer(text))
    if not matches:
        print("No ```mermaid fences found — nothing to do.")
        return

    slug = mdx_path.stem
    image_dir = REPO_ROOT / "public" / "static" / "images" / slug
    image_dir.mkdir(parents=True, exist_ok=True)

    # Number diagrams after whatever's already in image_dir, so re-running
    # this on a post that has some fences already converted (a likely
    # real-world case) can't silently overwrite an earlier diagram-N.png
    # that's referenced elsewhere in the file.
    existing = [int(p.stem.split("-")[1]) for p in image_dir.glob("diagram-*.png")
                if p.stem.split("-")[1].isdigit()]
    start_n = max(existing, default=0) + 1

    out = []
    last_end = 0
    for offset, m in enumerate(matches):
        n = start_n + offset
        out.append(text[last_end:m.start()])
        mermaid_src = m.group(1)
        print(f"Rendering diagram {offset + 1}/{len(matches)} (as diagram-{n}.png)...")
        png_bytes = render_png(mermaid_src, args.width, args.bg)
        img_path = image_dir / f"diagram-{n}.png"
        img_path.write_bytes(png_bytes)
        web_path = f"/static/images/{slug}/diagram-{n}.png"
        out.append(f"<center>![Diagram {n}]({web_path})</center>")
        last_end = m.end()
    out.append(text[last_end:])

    backup_path = mdx_path.with_suffix(mdx_path.suffix + ".bak")
    backup_path.write_text(text)
    mdx_path.write_text("".join(out))

    print(f"Rendered {len(matches)} diagram(s) into {image_dir}")
    print(f"Updated {mdx_path} (backup at {backup_path})")
    print("NOTE: replace the generic 'Diagram N' alt text with a real description, "
          "and delete the .bak file once you've checked the result.")


if __name__ == "__main__":
    main()
