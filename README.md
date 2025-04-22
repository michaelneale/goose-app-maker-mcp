# MCP for helping make and serve web apps

This will let users make html/js/rich web apps, which can be hosted statically, and or hosted statically with localhost data endpoints.

It allows serving up of apps on localhost which can access locally running services which this MCP runs.

# Usage from source

## Running from cli

# optional build in a clean environment using uv
```sh
uv venv .venv
source .venv/bin/activate
uv pip install build
python -m build
```


```sh
uv --directory $PWD run python main.py
```

### Building and Publishing

1. Update version in `pyproject.toml`:

```toml
[project]
version = "x.y.z"  # Update this
```

2. Build the package:

```bash
# Clean previous builds
rm -rf dist/*



3. Publish to PyPI:

```bash
# Install twine if needed
uv pip install twine

# Upload to PyPI
python -m twine upload dist/*
```
