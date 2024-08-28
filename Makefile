@PHONY: preview render setup_python_venv publish_manual clean

preview:
	quarto preview . --no-browser --port 54321

render:
	quarto render

setup_python_venv:
	pip freeze | xargs pip uninstall -y
	pip install -r requirements.txt
	pip freeze > requirements_snapshot.txt

publish_manual:
	# use this to manually update gh-pages
	quarto publish gh-pages

clean:
	# you can pass a --dry-run flag to do it as a dry run
	# delete files in the ignore file
	git clean -dfx --exclude "venv/" --exclude ".conda/"
