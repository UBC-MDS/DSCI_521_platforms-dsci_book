@PHONY: preview render setup_python_venv

preview:
	quarto preview . --no-browser --port 54321

setup_python_venv:
	pip freeze | xargs pip uninstall -y
	pip install ipykernel jupyter numpy matplotlib
	pip freeze > requirements.txt
