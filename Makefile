ROOT := $(shell pwd)

.PHONY: coverage docs mypy ruff-check ruff-fix ruff-format test test-plugin test-plugin-strict tox
.PHONY: publish-to-pypi rstcheck self-check

coverage:
	coverage run -m pytest tests
	coverage report -m

coverage-html:
	coverage run -m pytest tests
	coverage html

docs:
	cd "$(ROOT)"/docs && make clean && make html

mypy:
	mypy src/ tests/

pre-commit:
	pre-commit run --all-files

publish-to-pypi:
	uv build
	twine upload dist/*

# NOTE: to avoid rstcheck to fail on info-level messages, we set the report-level to WARNING
rstcheck:
	rstcheck --report-level=WARNING -r docs/

ruff-check:
	ruff check src tests

ruff-fix:
	ruff check --fix src tests

ruff-format:
	ruff format src tests

self-check:
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass src/
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass,protected-access,import-outside-toplevel,unused-variable,redefined-outer-name,reimported,unspecified-encoding,use-implicit-booleaness-not-comparison,unsorted-methods,function-should-be-private,too-many-public-methods tests/

test:
	pytest tests/

# Test plugin with relaxed rules for test files (matches pre-commit behavior)
test-plugin:
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass src/
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass,protected-access,import-outside-toplevel,unused-variable,redefined-outer-name,reimported,unspecified-encoding,use-implicit-booleaness-not-comparison,unsorted-methods,function-should-be-private,too-many-public-methods tests/

# Test plugin with strict rules for both src and test files (shows all warnings)
test-plugin-strict:
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass src/
	pylint --load-plugins=pylint_sort_functions --disable=fixme,unnecessary-pass tests/

tox:
	tox

view-docs:
	@xdg-open "file://$(ROOT)/docs/_build/html/index.html"
