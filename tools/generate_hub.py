#!/usr/bin/env python3
"""The umbrella site's own management: generate the hub, and check the whole tree.

This file belongs to the *site* repository -- the top level of
smallmade.github.io -- not to any application. It is deliberately self-contained:
standard library only, no import from any product repository, so it keeps working
unchanged when this folder is lifted out to become that repository.

The hierarchy it manages:

    <site root>/
        README.md          the rules (top-level management)
        apps.toml          the portfolio manifest (top-level management)
        tools/             this file (top-level management)
        index.html         the hub -- generated here, listing every compartment
        <slug>/            one compartment per application, written and owned by
                           that application's own repository; the top level never
                           reaches inside one, and no compartment reaches up

Two ways to run it:

    python3 tools/generate_hub.py            # rewrite index.html from apps.toml
    python3 tools/generate_hub.py --check    # verify everything; exit 1 on any lie

`--check` is the portfolio's gate, and what it refuses to pass is the whole reason
the top level exists: a card claiming an application is published whose two pages
are not actually there -- which, once deployed, is a 404 on the Support and Privacy
URLs App Store Connect holds for the life of that app.
"""

from __future__ import annotations

import argparse
import html
import pathlib
import re
import sys
import tomllib

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
MANIFEST = SITE / "apps.toml"
HUB = SITE / "index.html"

#: Where a reader writes, shown on the hub. Kept here, not imported from any
#: product: the address belongs to the portfolio. `--check` refuses a placeholder.
SUPPORT_EMAIL = "softwareone.support@gmail.com"

#: The name at the top of the hub. Not a company: this is a person publishing
#: software, and claiming otherwise on a page Apple reads is the kind of small
#: untruth that is expensive to have to correct later.
TITLE = "Software"

#: A copy of the pages' shared look, not an import of it. The product repositories
#: carry the same palette in their own generators; duplicating a stylesheet across
#: repository boundaries is the price of the boundary, and it is the right price --
#: an import back into a product repo would make the portfolio's front page depend
#: on one product's internals, which is the tangle this file exists to prevent.
STYLE = """
:root {
  --ink: #14171c; --dim: #5b626c; --line: #dfe3e8; --bg: #ffffff;
  --panel: #f6f8fa; --accent: #b8440e; --accent-ink: #ffffff;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e6e9ee; --dim: #9aa1ab; --line: #2b3038; --bg: #16181c;
    --panel: #1e2126; --accent: #ff8a5c; --accent-ink: #16181c;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.wrap { max-width: 880px; margin: 0 auto; padding: 0 24px; }
header { padding: 72px 0 40px; }
h1 { font-size: 2.6rem; line-height: 1.15; margin: 0 0 12px; letter-spacing: -0.02em; }
.lede { font-size: 1.2rem; color: var(--dim); margin: 0 0 28px; max-width: 60ch; }
h2 { font-size: 1.5rem; margin: 56px 0 14px; letter-spacing: -0.01em; }
p { max-width: 68ch; }
a { color: var(--accent); }
.apps { list-style: none; padding: 0; margin: 32px 0 0; }
.apps li {
  border: 1px solid var(--line); border-radius: 10px;
  padding: 22px 24px; margin: 0 0 16px; background: var(--panel);
}
.apps h2 { font-size: 1.3rem; margin: 0 0 6px; }
.apps p { margin: 0 0 14px; color: var(--dim); }
.meta { font-size: 0.85rem; color: var(--dim); }
.links a { margin-right: 18px; }
.soon { opacity: 0.62; }
footer { margin: 72px 0 56px; padding-top: 24px; border-top: 1px solid var(--line);
         color: var(--dim); font-size: 0.9rem; }
"""

#: What every manifest entry must state, and the shape a slug must have. The slug
#: becomes a path segment in URLs Apple stores for the life of the app, so it is
#: lowercase-hyphen and, once an app is submitted, permanent.
FIELDS = ("slug", "name", "tagline", "platforms", "status")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def manifest() -> list[dict[str, str]]:
    with MANIFEST.open("rb") as handle:
        return tomllib.load(handle).get("app", [])


def entry(app: dict[str, str]) -> str:
    slug, name = esc(app["slug"]), esc(app["name"])
    tagline = esc(app.get("tagline", ""))
    platforms = esc(app.get("platforms", ""))
    if app.get("status") == "published":
        links = (
            f'<p class="links"><a href="{slug}/support.html">Support</a>'
            f'<a href="{slug}/privacy.html">Privacy policy</a></p>'
        )
        classes = ""
    else:
        # Listed but not linked. A card whose Support link 404s is worse than a
        # card that says the app is not out yet.
        links = '<p class="meta">Not released yet.</p>'
        classes = ' class="soon"'
    return (
        f"<li{classes}><h2>{name}</h2>"
        f"<p>{tagline}</p>"
        f'<p class="meta">{platforms}</p>'
        f"{links}</li>"
    )


def hub(apps: list[dict[str, str]]) -> str:
    cards = "\n".join(entry(app) for app in apps)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TITLE)}</title>
<meta name="description" content="Support and privacy for the applications published
 here.">
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>{esc(TITLE)}</h1>
  <p class="lede">Support and privacy for each application published here. Every one
  of them runs entirely on your own device.</p>
</header>

<ul class="apps">
{cards}
</ul>

<h2>Getting help</h2>
<p>Write to <a href="mailto:{esc(SUPPORT_EMAIL)}">{esc(SUPPORT_EMAIL)}</a>, and say
which application you are writing about.</p>

<h2>Refunds</h2>
<p>Purchases are made from Apple, so refunds are Apple's to give. Go to
<a href="https://reportaproblem.apple.com">reportaproblem.apple.com</a> and sign in
with the Apple Account that made the purchase.</p>

<footer>
<p>This page collects nothing. It sets no cookie, loads no script, and requests
nothing from anywhere else. Each application has its own privacy policy, linked
above, because each application is its own answer to that question.</p>
</footer>

</div>
</body>
</html>
"""


def check(apps: list[dict[str, str]]) -> list[str]:
    """Every way the site can lie, as a list of the lies found."""
    wrong: list[str] = []

    if not apps:
        wrong.append("apps.toml lists nothing, so the hub would be an empty page")

    slugs = [app.get("slug", "") for app in apps]
    for slug in {s for s in slugs if slugs.count(s) > 1}:
        wrong.append(f"two applications share the slug {slug!r}")

    for app in apps:
        slug = app.get("slug", "?")
        for field in FIELDS:
            if not app.get(field):
                wrong.append(f"{slug}: {field} is missing or empty")
        if app.get("slug") and not SLUG.fullmatch(app["slug"]):
            wrong.append(f"{slug!r} is not a lowercase-hyphen slug, and it becomes a URL")

    body = HUB.read_text(encoding="utf-8") if HUB.is_file() else ""
    if not body:
        wrong.append("index.html is missing -- run tools/generate_hub.py")

    for app in apps:
        slug = app.get("slug", "")
        if app.get("status") == "published":
            for page in ("support.html", "privacy.html"):
                if not (SITE / slug / page).is_file():
                    wrong.append(
                        f"{slug} is marked published but {slug}/{page} is not there "
                        f"-- that is a 404 on a URL App Store Connect holds"
                    )
        else:
            if f'href="{slug}/' in body:
                wrong.append(f"{slug} is not released but the hub links into it")
            if app.get("name") and app["name"] not in body:
                wrong.append(f"{slug} is missing from the hub entirely")

    for target in re.findall(r'href="(?!https?:|mailto:)([^"#]+)"', body):
        if not (SITE / target).resolve().is_file():
            wrong.append(f"the hub links to missing {target}")

    if body and body != hub(apps):
        wrong.append("index.html is stale -- run tools/generate_hub.py")

    if "@" not in SUPPORT_EMAIL or SUPPORT_EMAIL == "SUPPORT_EMAIL":
        wrong.append("SUPPORT_EMAIL is not an address")

    if (SITE / "privacy.html").exists():
        wrong.append(
            "a privacy policy at the site root would be a policy for no particular "
            "app; each compartment carries its own"
        )
    return wrong


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true",
        help="verify the manifest, the hub and every compartment; write nothing",
    )
    args = parser.parse_args(argv)
    apps = manifest()

    if args.check:
        wrong = check(apps)
        for line in wrong:
            print(f"  WRONG: {line}", file=sys.stderr)
        print(f"  {'FAILED' if wrong else 'ok'} -- "
              f"{len(apps)} app(s), {len(wrong)} problem(s)")
        return 1 if wrong else 0

    HUB.write_text(hub(apps), encoding="utf-8")
    listed = ", ".join(app["slug"] for app in apps)
    print(f"  wrote index.html listing {len(apps)}: {listed}")
    wrong = check(apps)
    for line in wrong:
        print(f"  WRONG: {line}", file=sys.stderr)
    return 1 if wrong else 0


if __name__ == "__main__":
    raise SystemExit(main())
