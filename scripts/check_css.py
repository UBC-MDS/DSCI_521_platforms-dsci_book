"""Light/dark theme checks against the rendered site.

Run with `make check_css`, after `make render`. Reads only what Quarto wrote to
`_site/`, so it needs no browser and no extra dependencies -- Pillow arrives
with matplotlib.

Five checks, described where each one is defined:

  A  text colours against their own mode's background          -> hard failure
  B  colour variables that are the same in both colour modes   -> warning
  C  constructs the conventions page does not cover            -> note
  D  generated figures with a baked-in light background        -> warning
  E  listings that break the fence conventions                 -> note

Only check A can fail the build. B, C, D and E are judgement calls: they point
at something to look at, not something that is definitely wrong.

E is the odd one out: it reads the `.qmd` sources rather than `_site/`, because
what it checks -- which fence a listing uses -- is a property of the source that
the rendered page has already resolved away.

What this does NOT cover: anything needing a real browser and computed styles,
i.e. contrast of actual rendered text (as opposed to the variables that feed
it), focus rings, and horizontal overflow. Those need a headless browser, which
would mean a new dependency, so they stay manual for now.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path("_site")
CONVENTIONS = SITE / "lectures" / "book-conventions.html"

# The page background in each mode, from `_brand.yml` (`color.background`).
# Keep in sync if those change.
BG = {"light": "#ffffff", "dark": "#001328"}


# ---------------------------------------------------------------- colour math


def _luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


# ------------------------------------------------------------ reading the css


def linked_bundles(page: Path) -> dict[str, Path]:
    """Find the two Bootstrap stylesheets a rendered page actually links.

    `_site/site_libs/bootstrap/` accumulates stylesheets from earlier renders,
    and their names are content hashes, so globbing that directory and taking
    the newest or the alphabetically-last one will silently pick a stale build.
    Read the `<link>` tags instead -- those are by definition the current pair.
    """
    html = page.read_text(encoding="utf-8")
    out = {}
    for mode, pattern in (
        ("light", r'href="([^"]*bootstrap-[0-9a-f]+\.min\.css)"[^>]*data-mode="light"'),
        ("dark", r'href="([^"]*bootstrap-dark-[0-9a-f]+\.min\.css)"'),
    ):
        m = re.search(pattern, html)
        if not m:
            sys.exit(f"could not find the {mode} bootstrap bundle linked from {page}")
        href = m.group(1)
        out[mode] = SITE / href[href.index("site_libs/") :]
    return out


def root_variables(css: Path) -> dict[str, str]:
    """Map every `--bs-*` colour variable to its page-level value.

    Takes the FIRST occurrence of each name deliberately. Both bundles end with
    Bootstrap's own `[data-bs-theme="dark"]` block, which Quarto only ever
    scopes to the navbar -- so the last occurrence of, say, `--bs-body-color` is
    the navbar's value, not the page's. Reading it would make the light bundle
    look like it had dark-mode colours in it.
    """
    values: dict[str, str] = {}
    for name, value in re.findall(
        r"(--bs-[a-z0-9-]+): *(#[0-9a-fA-F]{3,6})\b", css.read_text(encoding="utf-8")
    ):
        values.setdefault(name, value)
    return values


# --------------------------------------------------------------------- checks

# Variables that paint text directly onto the page background. Anything that
# paints onto a component's own fill (a button, a badge, an active pill) is
# excluded, because its contrast is against that fill, not against the page.
PAGE_TEXT_VARIABLES = [
    "--bs-body-color",
    "--bs-emphasis-color",
    "--bs-heading-color",
    "--bs-link-color",
    "--bs-code-color",
    "--bs-secondary-color",
    "--bs-tertiary-color",
    "--bs-nav-tabs-link-active-color",
]


def check_text_contrast(bundles: dict[str, Path]) -> list[str]:
    """A: every page-level text colour must clear WCAG AA on its own background.

    This is the check that would have caught the invisible `.panel-tabset` tab,
    where `--bs-nav-tabs-link-active-color` and the page background were both
    #001328.
    """
    failures = []
    print("A. text colours vs. their own background")
    for mode, css in bundles.items():
        values = root_variables(css)
        for name in PAGE_TEXT_VARIABLES:
            if name not in values:
                continue
            ratio = contrast(values[name], BG[mode])
            ok = ratio >= 4.5
            print(
                f"     {mode:5s} {name:34s} {values[name]:9s} {ratio:6.2f}:1"
                f"  {'ok' if ok else 'FAIL'}"
            )
            if not ok:
                failures.append(
                    f"{name} is {values[name]} in {mode} mode, {ratio:.2f}:1 against "
                    f"{BG[mode]} (needs 4.5:1)"
                )
    return failures


# Bootstrap variables that are a *palette*, not a *role*: a fixed set of hues
# plus the grey ramp and the theme-colour names. These are supposed to hold one
# value in both modes -- `--bs-white` being white in dark mode is not a bug --
# so they would otherwise drown out the handful that genuinely should adapt.
PALETTE_VARIABLE = re.compile(
    r"^--bs-("
    r"white|black|gray|gray-dark|gray-\d{3}"
    r"|blue|indigo|purple|pink|red|orange|yellow|green|teal|cyan"
    r"|primary|secondary|success|info|warning|danger|light|dark"
    r")(-(text-emphasis|bg-subtle|border-subtle|rgb))?$"
)


def check_mode_symmetry(bundles: dict[str, Path], rendered_classes: set[str]) -> None:
    """B: role colours that are byte-identical in both bundles.

    Quarto compiles the two stylesheets as separate Bootstrap builds, both with
    light-mode defaults, so anything Bootstrap derives from `$gray-*` or
    `$black` keeps its light-mode value in the dark build too. This is how the
    borders ended up near-white on the dark page.

    Two filters keep the output readable. Palette names are dropped, because
    they are meant to be fixed. So are variables belonging to a component the
    book never renders -- there is no point reporting `--bs-modal-*` when
    nothing in the book is a modal.
    """
    light, dark = root_variables(bundles["light"]), root_variables(bundles["dark"])
    suspects = []
    for name, value in dark.items():
        if light.get(name) != value or PALETTE_VARIABLE.match(name):
            continue
        # `--bs-nav-tabs-link-active-color` -> does anything render `.nav-tabs`?
        stem = name[len("--bs-") :]
        parts = stem.split("-")
        prefixes = {"-".join(parts[:n]) for n in (1, 2)}
        if prefixes.isdisjoint(rendered_classes | {"border", "body", "emphasis", "link"}):
            continue
        cl, cd = contrast(value, BG["light"]), contrast(value, BG["dark"])
        if max(cl, cd) / min(cl, cd) >= 3:
            suspects.append((max(cl, cd) / min(cl, cd), name, value, cl, cd))
    print(f"\nB. role colours identical in both modes but reading very differently "
          f"({len(suspects)})")
    for _, name, value, cl, cd in sorted(suspects, reverse=True):
        print(f"     {name:38s} {value:9s} light {cl:5.2f}:1   dark {cd:5.2f}:1")
    if not suspects:
        print("     none")


CHROME = re.compile(
    r"^(quarto-|sidebar|navbar|nav-|toc|menu|page-|aa-|bi$|bi-|headroom|d-|py-|px-"
    r"|mb-|mt-|ms-|me-|col|row|container|btn|dropdown|collapse|active|show|fixed"
    r"|anchor|reveal|slide|jp-|footer|level\d|zindex)"
)


def _classes(page: Path) -> set[str]:
    body = page.read_text(encoding="utf-8", errors="replace").split("<body", 1)[-1]
    return {c for m in re.finditer(r'class="([^"]+)"', body) for c in m.group(1).split()}


def book_pages() -> list[Path]:
    """Pages Quarto wrote for this book.

    `site_libs/` holds vendored HTML shipped by revealjs and friends (the
    speaker-notes window, for one). It is not our markup and not styled by our
    theme, so it would only add noise.
    """
    return [p for p in sorted(SITE.rglob("*.html")) if "site_libs" not in p.parts]


def all_rendered_classes() -> set[str]:
    return {c for page in book_pages() for c in _classes(page)}


def check_conventions_coverage() -> None:
    """C: what the book renders that the conventions page does not.

    The conventions page is only evidence for the constructs actually on it, so
    this diffs its classes against every other page. Anything listed here is a
    construct no theme change is being checked against.
    """
    if not CONVENTIONS.exists():
        print("\nC. conventions coverage: page not built, skipped")
        return
    covered = _classes(CONVENTIONS)
    missing: dict[str, str] = {}
    for page in book_pages():
        # Slide decks are revealjs, a different format with its own theme and
        # its own class vocabulary (`navigate-left`, `controls-arrow`, ...).
        # An HTML conventions page cannot stand in for them, so diffing against
        # it only produces noise. They do get the brand -- fonts and palette
        # both reach the reveal theme -- they just are not checked here.
        if page == CONVENTIONS or 'class="reveal"' in page.read_text(
            encoding="utf-8", errors="replace"
        ):
            continue
        for name in _classes(page) - covered:
            if not CHROME.match(name):
                missing.setdefault(name, str(page.relative_to(SITE)))
    print(f"\nC. rendered by the book, absent from the conventions page "
          f"({len(missing)})")
    for name, where in sorted(missing.items())[:15]:
        print(f"     {name:26s} first seen in {where}")
    if len(missing) > 15:
        print(f"     ... and {len(missing) - 15} more")


def check_figure_plates() -> None:
    """D: generated figures carrying a light background into dark mode.

    A PNG written by matplotlib has its background baked in, so no stylesheet
    can adapt it -- on the dark page it shows as a white plate. Only figures
    produced by code cells are checked: static screenshots under `img/` are
    light by nature and cannot be fixed from here anyway.
    """
    try:
        from PIL import Image
    except ImportError:
        print("\nD. figure backgrounds: Pillow unavailable, skipped")
        return
    referenced = set()
    for page in book_pages():
        html = page.read_text(encoding="utf-8", errors="replace")
        for src in re.findall(r'<img[^>]*src="([^"]+)"', html):
            if "figure-" in src:
                referenced.add((page.parent / src).resolve())
    figures = [p for p in SITE.rglob("*_files/figure-*/*.png") if p.resolve() in referenced]
    flagged = []
    for path in figures:
        with Image.open(path) as im:
            im = im.convert("RGBA")
            w, h = im.size
            corners = [im.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
        if all(c[3] > 200 for c in corners):
            mean = sum(sum(c[:3]) / 3 for c in corners) / 4
            if contrast("#%02x%02x%02x" % ((int(mean),) * 3), BG["dark"]) >= 3:
                flagged.append((path.relative_to(SITE), int(mean)))
    print(f"\nD. generated figures with an opaque light background "
          f"({len(flagged)} of {len(figures)})")
    for path, mean in flagged:
        print(f"     {path}  (corner luma {mean})")
    if figures and not flagged:
        print("     none")
    if not figures:
        print("     no generated figures found")


# ------------------------------------------------------------ listing fences

# A fence opener: ```bash, ```out, ```{.python filename="penguins.py"}.
FENCE = re.compile(r"^(\s*)(`{3,})\s*(.*)$")
# `$ ` is the only shell prompt in the book. `❯` and `›` appear as the cursor of
# an interactive menu (`quarto create project`), which is output, not a prompt.
SHELL_PROMPT = re.compile(r"^\s*\$ ")
# Languages whose blocks say where they belong with an explicit `filename`.
# `bash` and `out` are excluded: `code-labels.lua` labels those.
WANTS_FILENAME = {"python", "r", "toml", "json", "default"}


def source_pages() -> list[Path]:
    return sorted(
        p for p in Path(".").rglob("*.qmd")
        if not {"_site", "_book", ".quarto"} & set(p.parts)
    )


def check_listing_fences() -> None:
    """E: listings that break the conventions page's rules for fences.

    Two rules, both from `lectures/0-conventions.qmd`:

      * a `bash` block is a command a student copies and runs, so it holds no
        prompt and no output -- the output is a separate `out` block;
      * a language with no automatic label carries a `filename` saying where its
        contents belong.

    Advisory, like B/C/D. The second rule has judgement in it -- a snippet that
    genuinely belongs nowhere in particular is a fair exception -- so this
    points at blocks to look at, not blocks that are definitely wrong.
    """
    prompts, unlabelled = [], []
    for page in source_pages():
        lines = page.read_text(encoding="utf-8", errors="replace").splitlines()
        i = 0
        while i < len(lines):
            m = FENCE.match(lines[i])
            if not m:
                i += 1
                continue
            ticks, info = m.group(2), m.group(3).strip()
            j = i + 1
            while j < len(lines):
                m2 = FENCE.match(lines[j])
                if m2 and not m2.group(3) and len(m2.group(2)) >= len(ticks):
                    break
                j += 1
            body = lines[i + 1 : j]

            if info == "bash":
                if any(SHELL_PROMPT.match(b) for b in body):
                    prompts.append(f"{page}:{i + 1}")
            elif info in WANTS_FILENAME:
                unlabelled.append(f"{page}:{i + 1}  ```{info}")
            i = j + 1

    print(f"\nE. `bash` listings holding a prompt or its output ({len(prompts)})")
    for where in prompts[:15]:
        print(f"     {where}")
    if not prompts:
        print("     none")

    print(f"\n   listings whose language has no automatic label and no "
          f"`filename` ({len(unlabelled)})")
    for where in unlabelled[:15]:
        print(f"     {where}")
    if len(unlabelled) > 15:
        print(f"     ... and {len(unlabelled) - 15} more")
    if not unlabelled:
        print("     none")


def main() -> int:
    if not SITE.is_dir():
        sys.exit("no _site/ -- run `make render` first")
    reference = CONVENTIONS if CONVENTIONS.exists() else next(SITE.rglob("*.html"))
    bundles = linked_bundles(reference)
    print(f"stylesheets linked by {reference.relative_to(SITE)}:")
    for mode, css in bundles.items():
        print(f"     {mode:5s} {css.name}")
    print()

    failures = check_text_contrast(bundles)
    check_mode_symmetry(bundles, all_rendered_classes())
    check_conventions_coverage()
    check_figure_plates()
    check_listing_fences()

    print()
    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print(f"   {f}")
        return 1
    print("no failures. B, C, D and E above are advisory -- read them, do not "
          "just count them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
