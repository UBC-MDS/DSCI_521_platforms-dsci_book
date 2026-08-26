# DSCI_521_platforms-dsci_book

[![Build and Publish Quarto Website](https://github.com/UBC-MDS/DSCI_521_platforms-dsci_book/actions/workflows/publish.yml/badge.svg)](https://github.com/UBC-MDS/DSCI_521_platforms-dsci_book/actions/workflows/publish.yml)
[![pages-build-deployment](https://github.com/UBC-MDS/DSCI_521_platforms-dsci_book/actions/workflows/pages/pages-build-deployment/badge.svg?branch=gh-pages)](https://github.com/UBC-MDS/DSCI_521_platforms-dsci_book/actions/workflows/pages/pages-build-deployment)
[![Check Links](https://github.com/UBC-MDS/DSCI_521_platforms-dsci_book/actions/workflows/check-links.yml/badge.svg)](https://github.com/UBC-MDS/DSCI_521_platforms-dsci_book/actions/workflows/check-links.yml)

## For the instructor

A few instructions/references for the instructor

### Convert old Jupyter Book content

Convert older `.ipynb` jupyter book files

```
quarto convert notebook.ipynb # will default convert to qmd
```

You might get conversion errors since jupyter allows `---` as a separator
and div.
This causes markdown to have errors since `---` is how markdown documents
specify the YAML header.

You can then use the generated `.qmd` file in the quarto website.

### Rendering the site locally

Right now the `docs` and `_site` directory is ignored.
We will use github actions to render the site into the `gh-pages` branch (eventually).

To build the site locally, you can run

```
make preview
```

This will run `quarto preview` for you with a fixed port (makes it easier to restart).

You can also render the final static site using `quarto`

```
quarto render
```

This repo uses a quarto extension that you will find in the `_extensions` directory.
If you want to re-install the extension, you can with:

```bash
quarto add coatless-quarto/embedio
```

### Commit messages

🤖 Section written by Claud Opus 5

This repo uses [Conventional Commits](https://www.conventionalcommits.org):

```
type(scope): short summary in the imperative mood
```

Lowercase, no trailing period, aim for 50 characters or less.
The scope is optional; use it when it tells the reader
*where* the change landed and the type alone would not.

**Types.**
Examples marked with a checkmark are actual commits in this repo;
the rest are illustrative.

| Type | Use it for | Example |
| --- | --- | --- |
| `feat` | new content or capability a reader will notice | ✅ `feat(order): re-order textbook TOC for 2026-27` |
| `fix` | something was broken and now is not | `fix(deps): restore = in pyproject.toml name field` |
| `docs` | prose about the project, not the project itself | ✅ `docs(toc): move conda toc to older materials` |
| `refactor` | restructuring that leaves the content alone | `refactor(lectures): decouple URLs from lecture numbers` |
| `style` | formatting only — semantic line breaks, whitespace | `style(readings): apply semantic line breaks` |
| `build` | dependencies, lockfiles, render configuration | ✅ `build(deps): flatten groups and upgrade deps` |
| `ci` | GitHub Actions workflows | ✅ `ci: pin R to 4.5.1 to match renv.lock` |
| `chore` | housekeeping with no effect on the built book | ✅ `chore: update renv` |
| `perf` | make something faster | `perf(render): cache the freeze directory` |
| `test` | adding or fixing checks | `test(links): add external link checker` |

**Scopes** that come up often here:

| Scope | Means |
| --- | --- |
| `deps` | `pyproject.toml`, `uv.lock`, `DESCRIPTION`, `renv.lock` |
| `toc` | the sidebar in `_quarto.yml` |
| `lectures` | anything under `lectures/` |
| `readings` | anything under `readings/` |
| `appendix` | anything under `appendix/` |
| `slides` | `lectures/demos/slides/` |
| `site` | theme, layout, `styles.scss`, render settings |
| `make` | the Makefile and the local build path |

Rule of thumb: pick the type by *why* the change was made,
not by which files it touched.
Bumping a package to fix a broken render is a `fix`, not a `build`.

**Breaking changes** get a `!` after the type
and a footer explaining what broke:

```
refactor(lectures)!: decouple rendered URLs from lecture numbers

BREAKING CHANGE: every published lecture URL changes.
No aliases were added, so links to lectures/*.html will 404.
```

For a textbook, "breaking" mostly means published URLs
and anything students have already bookmarked.

## Features of this repository

Technical features of this reporitory

- Built using `quarto`
- Uses `includes` to specify all the learning objectives and readings in a separate file
  so it can be included in multiple places
- custom css/scss for lecture activities and exercises

TODO:

- [ ] Auto build the book using github actions
- [ ] provide dockerfile for course packages and execution environment
- [ ] create slide content inline with the textbook lectures


## For students

How this book was made.
Every command below was actually run in this repository,
so you can line up what you do in class
with what the textbook does for itself.

### Python environment: uv

Create the project metadata without a package layout.
This writes `pyproject.toml`:

```bash
uv init --bare
```

Pin the Python version the book is built with.
This writes `.python-version`:

```bash
uv python pin 3.14
```

Add every package the book and the course need.
These all land under `dependencies` in `pyproject.toml`,
and the exact resolved versions are recorded in `uv.lock`:

```bash
uv add ipykernel jupyter jupyterlab jupyterlab-rise matplotlib numpy otter-grader rpy2
```

Everything goes in that one list on purpose.
`uv` can also split packages into optional groups,
but keeping a single list means there is exactly one install command to remember.

To recreate the environment on another machine,
which is the command you will use most:

```bash
uv sync
```

`uv sync` reads `uv.lock` and makes your environment match it exactly,
installing what is missing and removing what does not belong.

Run a command inside the environment
without activating it by hand:

```bash
uv run quarto render
```

### R environment: renv

Install the R version the book is built with (4.6.1):

The R packages the book needs are listed in `DESCRIPTION`, under `Imports`.
`renv/settings.json` sets `"snapshot.type": "explicit"`,
which means `renv.lock` is built from that list
rather than from scanning the `.qmd` files for `library()` calls.

Install those packages and record them in `renv.lock`:

```r
renv::install()
renv::snapshot()
```

To recreate the R library on another machine:

```r
renv::restore()
```

### The two lockfiles

`uv.lock` and `renv.lock` do the same job for the two languages.
`pyproject.toml` and `DESCRIPTION` record what the book *asks for*.
The lockfiles record what it actually *got*:
every package that was installed, at an exact version,
including the dependencies you never asked for by name.

That distinction is the whole point of a lockfile.
This repository is a live example of what goes wrong without one:
`renv.lock` pinned `base64enc` 0.1-3, which was fine for years,
until R 4.6 removed a C function that version relied on
and every build of the book broke at once.

### Building the book

```bash
make setup_python_env   # uv sync
make setup_r_env        # renv::restore()
make render             # uv run quarto render
```
