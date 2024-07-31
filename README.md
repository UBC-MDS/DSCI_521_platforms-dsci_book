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
