# Goose App Maker

This MCP (Model Context Protocol) sever allows users to create, manage, and serve web applications through Goose, that make use of Goose for api calls, data access, and more.

# Install

<a href="https://michaelneale.github.io/goose-redirect/?cmd=uvx&arg=app-maker-mcp@latest&id=goose-app-maker&name=Goose%20App%20Maker&description=Create%20and%20share%20apps%20that%20use%20goose">click here to install in goose 🪿 🪿🪿🪿🪿🪿🪿🪿🪿🪿 

</a>



## Features

- Create new web applications from basic instructions
- Store apps in `~/.config/goose/app-maker-apps` directory (each app in its own subdirectory)
- Serve web applications locally on demand
- Open web applications in the default browser (and chromeless if possible)
- Lists all available web applications
- make apps that can themselves use goose as a generic backend


## Examples 

### Load data via goose (re-using its extensions)

![Screenshot 2025-04-28 at 7 38 24 pm](https://github.com/user-attachments/assets/260e3c29-8aee-4492-87e5-7f20fe8a8e41)

![Screenshot 2025-04-28 at 7 38 53 pm](https://github.com/user-attachments/assets/473730e6-350c-4af2-8797-39b505b6748b)

<img width="400" alt="Screenshot 2025-04-28 at 7 35 46 pm" src="https://github.com/user-attachments/assets/4ddc14f8-7c83-4a1e-8e11-87c557355c9e" />

goose keeps track of your apps: 

<img width="682" alt="Screenshot 2025-04-28 at 7 35 46 pm" src="https://github.com/user-attachments/assets/6799833d-1edb-48f3-9061-656383f646fd" />


### Make apps on demand

<img width="400" alt="Screenshot 2025-04-28 at 6 24 09 pm" src="https://github.com/user-attachments/assets/5b2d0a5b-9012-4f67-80e1-e61641bdb45a" />

<img width="300" alt="Screenshot 2025-04-28 at 6 31 06 pm" src="https://github.com/user-attachments/assets/a856fc51-8476-4e39-afbb-99302f7e43c7" />



### Show rich tabular or list data as well

<img width="722" alt="Screenshot 2025-04-28 at 6 32 22 pm" src="https://github.com/user-attachments/assets/068e6dce-48b1-4fc0-b769-114961302d69" />


## Usage from source

eg in goose: 
```sh
# Run directly from source
uv --directory $PWD run python main.py
```

IMPORTANT: this MCP is required to be run in the goose desktop app at the moment (as it accesses goose-server/goosed)

## Building and publishing

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

# How it works

This MCP serves up apps, but also allows them to talk to goose via goosed and their own session: 

## Overview

The system implements a non-blocking, asynchronous request-response pattern that allows web applications to send requests to Goose and receive responses without blocking the main thread. This is achieved through a combination of:

1. A blocking endpoint on the server side
2. Asynchronous JavaScript on the client side
3. A response storage mechanism with thread synchronization

### Web App Structure

Web apps are made (or downloaded) on request, based on resources/templates. 
Each web app is stored in its own directory under `~/.config/goose/app-maker-apps` with the following structure:

```
app-name/
├── goose-app-manifest.json     # App metadata
├── index.html        # Main HTML file
├── style.css         # CSS styles
├── script.js         # JavaScript code
└── goose_api.js      # allows the apps to access goose(d) for deeper backend functionality
└── ...               # Other app files

```

The `goose-app-manifest.json` file contains metadata about the app, including:
- name: Display name of the app
- type: Type of app (e.g., "static", "react", etc.)
- description: Brief description of the app
- created: Timestamp when the app was created
- files: List of files in the app


### 1. Client-Side Request Flow

When a client wants to get a response from Goose:

```
┌─────────┐     ┌─────────────────┐     ┌───────────────┐     ┌──────────────┐
│ User    │────▶│ gooseRequestX() │────▶│ Goose API     │────▶│ waitForResp- │
│ Request │     │ (text/list/     │     │ (/reply)      │     │ onse endpoint │
└─────────┘     │  table)         │     └───────────────┘     └──────────────┘
                └─────────────────┘                                   │
                         ▲                                            │
                         │                                            │
                         └────────────────────────────────────────────┘
                                          Response
```

1. The user initiates a request (e.g., clicking "Get List Response")
2. The client calls one of the request functions (`gooseRequestText`, `gooseRequestList`, or `gooseRequestTable`)
3. The function generates a unique `responseId` and sends a request to Goose with instructions to call `app_response` with this ID
4. The function then calls `waitForResponse(responseId)` which polls the `/wait_for_response/{responseId}` endpoint
5. This endpoint blocks until the response is available or a timeout occurs
6. When the response is available, it's returned to the client and displayed

### 2. Server-Side Processing

On the server side:

```
┌─────────────┐     ┌─────────────┐     ┌───────────────┐
│ HTTP Server │────▶│ app_response│────▶│ response_locks│
│ (blocking   │     │ (stores     │     │ (notifies     │
│  endpoint)  │◀────│  response)  │◀────│  waiters)     │
└─────────────┘     └─────────────┘     └───────────────┘
```

1. The `/wait_for_response/{responseId}` endpoint uses condition variables to block until a response is available
2. When Goose processes the request, it calls the `app_response` function with the response data and the `responseId`
3. The `app_response` function stores the response in the `app_responses` dictionary and notifies any waiting threads using the condition variable
4. The blocked HTTP request is then unblocked and returns the response to the client

### 3. Thread Synchronization

The system uses Python's `threading.Condition` for thread synchronization:

1. When a client requests a response that isn't available yet, a condition variable is created for that `responseId`
2. The HTTP handler thread waits on this condition with a timeout (30 seconds)
3. When the response becomes available, the condition is notified
4. If the timeout expires before the response is available, an error is returned

## Key Components

### Client-Side Functions

- `gooseRequestText(query)`: Requests a text response
- `gooseRequestList(query)`: Requests a list response
- `gooseRequestTable(query, columns)`: Requests a table response with specified columns
- `waitForResponse(responseId)`: Waits for a response with the given ID

### Server-Side Functions

- `app_response(response_id, string_data, list_data, table_data)`: Stores a response and notifies waiters
- HTTP handler with `/wait_for_response/{responseId}` endpoint: Blocks until response is available
