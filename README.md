# Goose App Maker

This MCP (Model Context Protocol) servcer allows users to create, manage, and serve web applications through Goose.

## Features

- Create new web applications with custom HTML, CSS, and JavaScript
- Store apps in `~/.config/goose/app-maker-apps` directory (each app in its own subdirectory)
- Serve web applications locally on demand
- Open web applications in the default browser
- Update existing web application files
- List all available web applications
- Delete web applications
- resources dir for helper scripts and examples
- make apps that can themselves use goose
- share apps via things like google drive for you
- resources/goose_api.js which can be used in web apps that need to talk to goose api (web serve will provide creds just in time)

## Usage from source

```sh
# Run directly from source
uv --directory $PWD run python main.py
```

## Building and Installing

### Optional: Build in a clean environment using uv

```sh
uv venv .venv
source .venv/bin/activate
uv pip install build
python -m build
```

### Publishing

1. Update version in `pyproject.toml`:

```toml
[project]
version = "x.y.z"  # Update this
```

2. Build the package:

```bash
# Clean previous builds
rm -rf dist/*
python -m build
```

3. Publish to PyPI:

```bash
# Install twine if needed
uv pip install twine

# Upload to PyPI
python -m twine upload dist/*
```

## Web App Structure

Each web app is stored in its own directory under `~/.config/goose/app-maker-apps` with the following structure:

```
app-name/
├── goose-app-manifest.json     # App metadata
├── index.html        # Main HTML file
├── style.css         # CSS styles
├── script.js         # JavaScript code
└── ...               # Other app files
```

The `goose-app-manifest.json` file contains metadata about the app, including:
- name: Display name of the app
- type: Type of app (e.g., "static", "react", etc.)
- description: Brief description of the app
- created: Timestamp when the app was created
- files: List of files in the app
