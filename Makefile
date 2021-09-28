SHELL='/bin/bash'

tests:
	pytest -v

doc:
	sphinx-build docs docs/build

release:
	# move old releases
	mv dist/* archive 1>/dev/null 2>&1 || echo ""
	python setup.py sdist bdist_wheel

release-pypi:
	twine upload dist/*


