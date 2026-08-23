# smallmade.github.io

The umbrella site for every application published under this account. This
folder is the repository's entire content; it is staged inside the gas-dynamics
product repository only until the standalone site repository is created, and it
imports nothing from there.

## The hierarchy, and the one rule

```
<root>                     top-level management -- owned by this repository
├── README.md              these rules
├── apps.toml              the portfolio manifest
├── tools/generate_hub.py  generates index.html; --check gates the whole tree
├── index.html             the hub, generated -- never edited by hand
│
├── gas-dynamics/          a compartment -- owned by that app's own repository
└── <next-slug>/           a compartment -- owned by that app's own repository
```

**The rule: compartments and the top level never reach into each other.**

- A compartment owns exactly its own folder. Its product repository generates
  `support.html`, `privacy.html` and any assets, and copies them in. It never
  touches `apps.toml`, `index.html`, `tools/`, or another compartment.
- The top level owns the manifest, the hub and the checks. It lists compartments
  and verifies their two required pages *exist*; it never generates, edits or
  assumes anything about what is inside them.
- `tools/generate_hub.py` is standard-library-only and imports from no product
  repository, so the portfolio's front page can never break because one product
  refactored its internals.

Why compartments at all: App Store Connect holds a Support URL and a Privacy
Policy URL **per app**, for the life of the app, and a privacy policy must
describe the one app it belongs to. The folder name is that app's `slug` and is
therefore **permanent once the app is submitted** -- renaming it breaks URLs
Apple has already recorded.

## Adding an application

1. Add an entry to `apps.toml`:

   ```toml
   [[app]]
   slug = "the-new-app"
   name = "The New App"
   tagline = "One sentence about what it does."
   platforms = "Mac and iPad"
   status = "coming"          # -> "published" once its pages are in place
   ```

2. `python3 tools/generate_hub.py` -- the hub lists it, unlinked, as "not
   released yet". A card whose Support link 404s is worse than one that says the
   app is not out.

3. When that app's repository has copied its `slug/support.html` and
   `slug/privacy.html` in, flip `status` to `published` and regenerate.

4. `python3 tools/generate_hub.py --check` must print `ok` before any push.
   It fails on: a published app whose pages are missing, an unreleased app the
   hub links into, duplicate or malformed slugs, missing manifest fields, a
   stale or hand-edited hub, any dead link, and a placeholder support address.

## Deploying

GitHub Pages, from this repository: Settings → Pages → Deploy from a branch →
`main`, `/ (root)`. Everything in the folder deploys as-is; `apps.toml`,
`tools/` and this file ride along harmlessly -- they are small, public anyway,
and keeping them beside the pages is what makes the site self-managing.

After any push, confirm the URLs App Store Connect holds still answer:

```
curl -sI https://smallmade.github.io/gas-dynamics/privacy.html
```

`HTTP/2 200`, nothing else.
