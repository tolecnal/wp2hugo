build:
	python3 -m pip install build twine
	python3 -m build

confirm_build:
	twine check dist/*

publish_test:
	twine upload -r testpypi dist/*

publish_prod:
	twine upload dist/*

clean:
	rm -rf out/
	rm -rf dist/
