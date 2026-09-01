.PHONY: preview render check_css setup_python_env setup_r_env setup_quarto publish_manual clean

# Quarto ships its own pandoc, but the nested rmarkdown::render() call in
# lecture 4 looks for pandoc the way RStudio does and misses it.
# Point rmarkdown at the copy Quarto already has.
export RSTUDIO_PANDOC := $(shell find "$$(quarto --paths | head -1)/tools" -name pandoc -type f 2>/dev/null | head -1 | xargs dirname)

preview:
	uv run quarto preview . --no-browser --port 54321

render:
	uv run quarto render

check_css:
	# light/dark theme checks against the built site -- run `make render` first.
	# Only the text-contrast check can fail; the rest are advisory.
	uv run python scripts/check_css.py

setup_python_env:
	# build .venv from pyproject.toml + uv.lock
	uv sync

setup_r_env:
	# build renv/library from renv.lock
	Rscript -e 'renv::restore()'

setup_quarto:
	# install the Quarto extensions into _extensions/
	quarto add --no-prompt coatless-quarto/custom-callout
	quarto add --no-prompt coatless-quarto/embedio

publish_manual:
	# use this to manually update gh-pages
	uv run quarto publish gh-pages

clean:
	# you can pass a --dry-run flag to do it as a dry run
	# delete files in the ignore file
	git clean -dfx --exclude "venv/" --exclude ".venv/" --exclude ".conda/"
