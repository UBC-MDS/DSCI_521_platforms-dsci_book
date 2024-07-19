@PHONY: preview render setup_python_venv

preview:
	quarto preview . --no-browser --port 54321

setup_python_venv:
	pip install jupyter numpy matplotlib
