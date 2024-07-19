# DSCI_521_platforms-dsci_book

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
