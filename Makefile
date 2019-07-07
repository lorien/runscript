clean:
	find -name '*.pyc' -delete
	find -name '*.swp' -delete

upload:
	git push --tags; python setup.py clean sdist upload

test:
	./test.py

.PHONY: clean upload test
