.PHONY: build serve

build:
	uv run --script build.py build

serve:
	python3 -m http.server --directory _build 8000
