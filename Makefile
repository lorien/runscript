.PHONY: bootstrap venv deps dirs clean upload test release check

FILES_CHECK_MYPY = runscript runscript_gevent setup.py
FILES_CHECK_ALL = $(FILES_CHECK_MYPY) tests

bootstrap: venv deps dirs

venv:
	virtualenv -p python3 .env

deps:
	.env/bin/pip install -r requirements.txt
	.env/bin/pip install -e .

dirs:
	if [ ! -e var ]; then mkdir -p var; fi

clean:
	find -name '*.pyc' -delete
	find -name '*.swp' -delete

upload:
	git push --tags; python setup.py clean sdist upload

test:
	pytest

release:
	git push; git push --tags; rm dist/*; python3 setup.py clean sdist; twine upload dist/*

check:
	echo "mypy" \
	&& mypy --strict $(FILES_CHECK_MYPY) \
	&& echo "pylint" \
	&& pylint -j0 $(FILES_CHECK_ALL) \
	&& echo "flake8" \
	&& flake8 -j auto --max-cognitive-complexity=11 $(FILES_CHECK_ALL) \
	&& echo "bandit" \
	&& bandit -qc pyproject.toml -r $(FILES_CHECK_ALL) \
