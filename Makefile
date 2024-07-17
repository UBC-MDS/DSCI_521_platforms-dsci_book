@PHONY: preview render setup_python_venv

preview:
	quarto preview

setup_python_venv:
	pip install jupyter numpy matplotlib
