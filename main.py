from mcp.server.fastmcp import FastMCP
import os
import subprocess
import logging
import time
import json
import shutil
import http.server
import socketserver
import threading
from typing import Dict, Any, List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("Starting Goose App Maker MCP server...")

# Define the app storage directory
APP_DIR = os.path.expanduser("~/.config/goose/app-maker-apps")
os.makedirs(APP_DIR, exist_ok=True)
logger.info(f"Using app directory: {APP_DIR}")

# Define paths for resources
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(SCRIPT_DIR, "resources")
README_PATH = os.path.join(SCRIPT_DIR, "README.md")
GOOSE_API_PATH = os.path.join(RESOURCES_DIR, "kitchen-sink/goose_api.js")

# Global variable to store the HTTP server instance
http_server = None
server_port = 8000  # Default port

# Global variable to store app response
app_response = None
response_lock = threading.Condition()
response_ready = False

# Global variable to store app errors
app_errors = []

instructions = """
This extension allows creation and running of casual web apps for Goose.
You are an expert html5/CSS/js web app author for casual "apps" for goose. Use this toolkit when running/making apps for goose.

Your job is to help users create and manage web applications that are stored in the ~/.config/goose/app-maker-apps directory.
In some cases you will be creating from scratch (or building from other example app), or modifying an existing app
In other cases you will just be serving up an existing app that has been downloaded and is available (will not be need to be modified unless the user explicitaly asks to)
In some other cases you may just be answering a query/taking an action that an app requires and you may not need to edit the app.
The user may not be an professional developer (however they may indicate they are, based on how they interact with you, in which case, you may be working on apps using the devleoper extension).
This extension is to supplement goose for casual sharable goose apps.

You can also serve up apps via a built in server. 

You can:
1. Generate new web applications based on user requirements
2. Serve existing web applications locally
3. Modify existing web applications
4. List available web applications
5. Open web applications in the default browser
6. Take some existing web app/html and bring it into the app-maker-apps directory for serving.

When generating web apps:
- Create clean, modern, and responsive designs
- They should be beautiful and user-friendly
- Ensure proper HTML5, CSS, and JavaScript structure
- You can embed data in the app if it is static and non PII, and safe to do so
- Of course the usual html5 browser apis are available to you (such as fetch, local storage, etc)
- Use the goose_api.js when data needs to be dynamic (see below) for powerful data and api and agentic functionality
- Open the app as it is built with the default browser to show the user, and invite feedback
- Use other tools as available to assist in building the app (such as screenshot for visual review)

Each app is stored in its own directory within ~/.config/goose/app-maker-apps.

Once an app is created, you can modify or replace contents of its files using tools available. Typically there is an index.html, style.css, and script.js file (and the goose_api.js helper) - but you don't have to stick to this structure if you know better.

The directory ~/.config/goose/app-maker-apps/[app-name]/ is where the app is stored.

Resources:
- The resources directory is located at: {resources_dir} which has utilities and examples you can refer to.
- For example apps, refer to the examples in the [README.md]({readme_path})
- For apps requiring dynamic functionality or access to data sources/services, include [goose_api.js]({goose_api_path}) in your app

Using goose_api.js for dynamic content:
- Include it in your HTML: <script src="goose_api.js"></script>
- Use these functions to get responses from Goose:
  - gooseRequestText(query) - Returns a text/paragraph response
  - gooseRequestList(query) - Returns a list of items
  - gooseRequestTable(query, columns) - Returns tabular data (columns required)
- For error reporting:
  - reportError(errorMessage) - Reports errors back to Goose
- Example: const response = await gooseRequestList("List 5 best movies");
- See {readme_path} for more detailed examples
    
Some of the tools available:
  app_create - use this when starting new
  app_list - find existing apps 
  app_serve - serve an app locally
  app_open - open an app in a browser (macos)
  app_response - for sending data back to the app front end
  app_error - use this to see if there are error from the app, useful when modifying an app
"""

# Format the instructions with dynamic paths
instructions = instructions.format(
    resources_dir=RESOURCES_DIR,
    readme_path=README_PATH,
    goose_api_path=GOOSE_API_PATH
)

mcp = FastMCP("Goose App Maker", instructions=instructions)


@mcp.tool()
def app_list() -> Dict[str, Any]:
    """
    List all available web applications.
    
    Returns:
        A dictionary containing the list of available apps and their details
    """
    try:
        apps = []
        for app_dir in Path(APP_DIR).iterdir():
            if app_dir.is_dir():
                app_info = {
                    "name": app_dir.name,
                    "path": str(app_dir),
                    "files": []
                }
                
                # Get the list of files
                for file_path in app_dir.glob("**/*"):
                    if file_path.is_file():
                        rel_path = str(file_path.relative_to(app_dir))
                        app_info["files"].append(rel_path)
                
                # Check if there's a goose-app-manifest.json file
                manifest_path = app_dir / "goose-app-manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                            app_info["manifest"] = manifest
                    except json.JSONDecodeError:
                        app_info["manifest_error"] = "Invalid goose-app-manifest.json file"
                
                apps.append(app_info)
        
        return {
            "success": True,
            "apps": apps,
            "count": len(apps),
            "app_dir": APP_DIR
        }
    except Exception as e:
        logger.error(f"Error listing apps: {e}")
        return {"success": False, "error": f"Failed to list apps: {str(e)}"}
    

@mcp.tool()
def app_delete(app_name: str) -> Dict[str, Any]:
    """
    Delete an existing web application.
    
    Args:
        app_name: Name of the application to delete
    
    Returns:
        A dictionary containing the result of the operation
    """
    try:
        # Find the app directory
        app_path = os.path.join(APP_DIR, app_name)
        if not os.path.exists(app_path):
            return {
                "success": False, 
                "error": f"App '{app_name}' not found at {app_path}"
            }
        
        # Delete the app directory
        shutil.rmtree(app_path)
        
        return {
            "success": True,
            "app_name": app_name,
            "message": f"App '{app_name}' deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting app: {e}")
        return {"success": False, "error": f"Failed to delete app: {str(e)}"}


@mcp.tool()
def app_create(app_name: str, description: str = "") -> Dict[str, Any]:
    """
    Create a new web application directory and copy starter files.
    The starter files are for you to replace with actual content, you don't have to use them as is.
    the goose_api.js file is a utility you will want to keep in case you need to do api calls as part of your app via goose.
    
    Args:
        app_name: Name of the application (will be used as directory name)
        description: Brief description of the application (default: "")
    
    Returns:
        A dictionary containing the result of the operation

    After this, consider how you want to change the app to meet the functionality, look at the examples in resources dir if you like.
    Or, you can replace the content with existing html/css/js files you have (just make sure to leave the goose_api.js file in the app dir)

    Use the app_error tool once it is opened and user has interacted (or has started) to check for errors you can correct the first time, this is important to know it works.

    """
    global http_server, server_port

    if http_server:
        return "There is already a server running. Please stop it before creating a new app, or consider if an existing app should be modified instead."
    try:
        # Sanitize app name (replace spaces with hyphens, remove special characters)
        safe_app_name = "".join(c if c.isalnum() else "-" for c in app_name).lower()
        
        # Create app directory
        app_path = os.path.join(APP_DIR, safe_app_name)
        if os.path.exists(app_path):
            return {
                "success": False, 
                "error": f"App '{safe_app_name}' already exists at {app_path}"
            }
        
        os.makedirs(app_path, exist_ok=True)
        
        
        # Copy kitchen-sink template files
        kitchen_sink_dir = os.path.join(RESOURCES_DIR, "kitchen-sink")
        copied_files = ["index.html", "style.css", "script.js", "goose_api.js"]
        
        for file_name in copied_files:
            src_file = os.path.join(kitchen_sink_dir, file_name)
            dest_file = os.path.join(app_path, file_name)
            shutil.copy2(src_file, dest_file)
        
        # Create manifest file
        manifest = {
            "name": app_name,
            "description": description,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "files": copied_files
        }
        
        with open(os.path.join(app_path, "goose-app-manifest.json"), 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return {
            "success": True,
            "app_name": safe_app_name,
            "app_path": app_path,
            "files": copied_files,
            "message": f"App '{app_name}' created successfully at {app_path}"
        }
    except Exception as e:
        logger.error(f"Error creating app: {e}")
        return {"success": False, "error": f"Failed to create app: {str(e)}"}

@mcp.tool()
def app_serve(app_name: str) -> Dict[str, Any]:
    """
    Serve an existing web application on a local HTTP server.
    The server will automatically find an available port.

    Can only serve one app at a time
    
    Args:
        app_name: Name of the application to serve
    
    Returns:
        A dictionary containing the result of the operation
    """
    global http_server, server_port, app_response, response_ready

    if http_server:
        return "There is already a server running"

    # Reset response state
    app_response = None
    response_ready = False
    
    try:
        # Find the app directory
        app_path = os.path.join(APP_DIR, app_name)
        if not os.path.exists(app_path):
            return {
                "success": False, 
                "error": f"App '{app_name}' not found at {app_path}"
            }
        
        # Stop any existing server
        if http_server:
            logger.info("Stopping existing HTTP server")
            http_server.shutdown()
            http_server.server_close()
            http_server = None
        
        # Find a free port
        import socket
        def find_free_port():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                return s.getsockname()[1]
        
        # Try the default port first, if busy find a free one
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', server_port))
        except OSError:
            logger.info(f"Default port {server_port} is busy, finding a free port")
            server_port = find_free_port()
            logger.info(f"Found free port: {server_port}")
        
        # Create a custom handler that serves from the app directory
        # and replaces environment variables in JavaScript files
        class EnvAwareHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=app_path, **kwargs)
            
            def end_headers(self):
                # Add cache control headers to ALL responses
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                super().end_headers()
            
            def do_GET(self):
                # Check if this is a wait_for_response request
                if self.path.startswith('/wait_for_response'):
                    global app_response, response_lock, response_ready
                    
                    # Reset response state for a new request
                    if self.path.startswith('/wait_for_response/reset'):
                        with response_lock:
                            app_response = None
                            response_ready = False
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        response_data = json.dumps({"success": True, "message": "Response state reset"})
                        self.wfile.write(response_data.encode('utf-8'))
                        return
                    
                    # Check if response already exists
                    if app_response is not None and response_ready:
                        # Return the response immediately
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        response_data = json.dumps({"success": True, "data": app_response})
                        self.wfile.write(response_data.encode('utf-8'))
                        
                        # Reset the response state after sending it
                        with response_lock:
                            app_response = None
                            response_ready = False
                        return
                    
                    # Wait for the response with timeout
                    with response_lock:
                        # Wait for up to 180 seconds for the response to be ready
                        start_time = time.time()
                        while not response_ready and time.time() - start_time < 180:
                            response_lock.wait(180 - (time.time() - start_time))
                            
                            # Check if the response is now available
                            if response_ready and app_response is not None:
                                break
                        
                        # Check if we got the response or timed out
                        if response_ready and app_response is not None:
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            response_data = json.dumps({"success": True, "data": app_response})
                            self.wfile.write(response_data.encode('utf-8'))
                        else:
                            # Timeout occurred
                            self.send_response(408)  # Request Timeout
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            response_data = json.dumps({"success": False, "error": "Timeout waiting for response"})
                            self.wfile.write(response_data.encode('utf-8'))
                    return
                
                # Get the file path
                path = self.translate_path(self.path)
                
                # Check if the file exists
                if os.path.isfile(path):
                    # Check if it's a JavaScript file that might need variable replacement
                    if path.endswith('.js'):
                        try:
                            with open(path, 'r') as f:
                                content = f.read()
                            
                            # Check if the file contains environment variables that need to be replaced
                            if '$GOOSE_PORT' in content or '$GOOSE_SERVER__SECRET_KEY' in content:
                                # Replace environment variables
                                goose_port = os.environ.get('GOOSE_PORT', '0')
                                secret_key = os.environ.get('GOOSE_SERVER__SECRET_KEY', '')
                                
                                # Replace variables
                                content = content.replace('$GOOSE_PORT', goose_port)
                                content = content.replace('$GOOSE_SERVER__SECRET_KEY', secret_key)
                                
                                # Send the modified content
                                self.send_response(200)
                                self.send_header('Content-type', 'application/javascript')
                                self.send_header('Content-Length', str(len(content)))
                                self.end_headers()
                                self.wfile.write(content.encode('utf-8'))
                                return
                        except Exception as e:
                            logger.error(f"Error processing JavaScript file: {e}")
                
                # If we didn't handle it specially, use the default handler
                return super().do_GET()
        
        # Start the server in a separate thread
        import threading
        
        # Use a thread-safe event to signal when the server is ready
        server_ready = threading.Event()
        server_error = [None]  # Use a list to store error from thread
        
        def run_server():
            global http_server
            try:
                with socketserver.TCPServer(("", server_port), EnvAwareHandler) as server:
                    http_server = server
                    # Signal that server is ready
                    server_ready.set()
                    logger.info(f"Serving app '{app_name}' at http://localhost:{server_port}")
                    logger.info(f"Using GOOSE_PORT={os.environ.get('GOOSE_PORT', '3000')}")
                    logger.info(f"Using GOOSE_SERVER__SECRET_KEY={os.environ.get('GOOSE_SERVER__SECRET_KEY', '')[:5]}...")
                    server.serve_forever()
            except Exception as e:
                server_error[0] = str(e)
                server_ready.set()  # Signal even on error
                logger.error(f"Server error: {e}")
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for the server to start or fail, with timeout
        if not server_ready.wait(timeout=2.0):
            return {
                "success": False,
                "error": "Server failed to start within timeout period"
            }
           
        # Check if there was an error
        if server_error[0]:
            return {
                "success": False,
                "error": f"Failed to serve app: {server_error[0]}"
            }
        
        return {
            "success": True,
            "app_name": app_name,
            "port": server_port,
            "url": f"http://localhost:{server_port}",
            "message": f"App '{app_name}' is now being served at http://localhost:{server_port}"
        }
    except Exception as e:
        logger.error(f"Error serving app: {e}")
        return {"success": False, "error": f"Failed to serve app: {str(e)}"}

@mcp.tool()
def app_stop_server() -> Dict[str, Any]:
    """
    Stop the currently running HTTP server.
    
    Returns:
        A dictionary containing the result of the operation
    """
    global http_server, app_response, response_ready
    
    try:
        if http_server:
            logger.info("Stopping HTTP server")
            http_server.shutdown()
            http_server.server_close()
            http_server = None
            
            # Reset response state
            app_response = None
            response_ready = False
            
            return {
                "success": True,
                "message": "HTTP server stopped successfully"
            }
        else:
            return {
                "success": False,
                "error": "No HTTP server is currently running"
            }
    except Exception as e:
        logger.error(f"Error stopping server: {e}")
        return {"success": False, "error": f"Failed to stop server: {str(e)}"}

@mcp.tool()
def app_open(app_name: str) -> Dict[str, Any]:
    """
    Open an app in the default web browser. If the app is not currently being served,
    it will be served first.
    Can only open one app at a time.
    
    Args:
        app_name: Name of the application to open
    
    Returns:
        A dictionary containing the result of the operation
    """
    global http_server
    
    try:
        # Find the app directory
        app_path = os.path.join(APP_DIR, app_name)
        if not os.path.exists(app_path):
            return {
                "success": False, 
                "error": f"App '{app_name}' not found at {app_path}"
            }
        
        # If the server is not running, start it
        if not http_server:
            serve_result = app_serve(app_name)
            if not serve_result["success"]:
                return serve_result
            # Get the URL from the serve result
            url = serve_result["url"]
        else:
            # Use the current server port
            url = f"http://localhost:{server_port}"
        
        # Check if we're on macOS
        if os.uname().sysname == "Darwin":  # macOS
            # Use Chrome in app mode
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(chrome_path):
                logger.info(f"Opening app in Chrome app mode: {url}")
                # Use Popen instead of run to avoid blocking
                subprocess.Popen([chrome_path, f"--app={url}"], 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
            else:
                # Fallback to default browser if Chrome is not installed
                logger.info(f"Chrome not found, opening in default browser: {url}")
                # Use Popen instead of run to avoid blocking
                subprocess.Popen(["open", url], 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
        else:
            # For non-macOS systems, use the default browser
            # Use Popen instead of run to avoid blocking
            subprocess.Popen(["open", url], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        
        return {
            "success": True,
            "app_name": app_name,
            "url": url,
            "message": f"App '{app_name}' opened in browser at {url}"
        }
    except Exception as e:
        logger.error(f"Error opening app: {e}")
        return {"success": False, "error": f"Failed to open app: {str(e)}"}

@mcp.tool()
def app_refresh() -> Dict[str, Any]:
    """
    Refresh the currently open app in Chrome.
    Only works on macOS with Google Chrome.
    
    Returns:
        A dictionary containing the result of the operation
    """
    try:
        # Check if we're on macOS
        if os.uname().sysname != "Darwin":
            return {
                "success": False,
                "error": "This function is only available on macOS"
            }
        
        # Use AppleScript to refresh the active tab in Chrome
        refresh_script = 'tell application "Google Chrome" to tell active tab of front window to reload'
        # Use Popen instead of run to avoid blocking
        subprocess.Popen(["osascript", "-e", refresh_script], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        
        return {
            "success": True,
            "message": "App refreshed successfully in Chrome"
        }
    except Exception as e:
        logger.error(f"Error refreshing app: {e}")
        return {"success": False, "error": f"Failed to refresh app: {str(e)}"}

@mcp.tool()
def app_response(string_data: str = None, 
                list_data: List[str] = None, 
                table_data: Dict[str, List] = None) -> bool:
    """
    Use this to return a response to the app that has been requested.
    Provide only one of string_data, list_data, or table_data.
    
    Args:
        string_data: Optional string response
        list_data: Optional list of strings response
        table_data: Optional table response with columns and rows
                    Format: {"columns": ["col1", "col2", ...], "rows": [["row1col1", "row1col2", ...], ...]}
    
    Returns:
        True if the response was stored successfully, False otherwise
    """
    global app_response, response_lock, response_ready
    
    try:
        # Check that exactly one data type is provided
        provided_data = [d for d in [string_data, list_data, table_data] if d is not None]
        if len(provided_data) != 1:
            logger.error("Exactly one of string_data, list_data, or table_data must be provided")
            return False
        
        # Determine the type of data and store it
        if string_data is not None:
            data = string_data
        elif list_data is not None:
            data = list_data
        elif table_data is not None:
            # Validate table_data format
            if not isinstance(table_data, dict) or "columns" not in table_data or "rows" not in table_data:
                logger.error("Table data must have 'columns' and 'rows' keys")
                return False
            data = table_data
        
        # Store the response and notify waiting threads
        with response_lock:
            global app_response  # Declare global inside the function block
            app_response = data
            global response_ready  # Declare global inside the function block
            response_ready = True
            response_lock.notify_all()
        
        return True
    except Exception as e:
        logger.error(f"Error storing response: {e}")
        return False

@mcp.tool()
def app_error(error_message: str = None, clear = False) -> str:
    """
    Report an error from the app or retrieve the list of errors.
    This is useful while developing or debugging the app as it allows errors (or any messages) to be reported and monitored
    
    Args:
        error_message: Optional error message to report. If None, returns the list of errors.
        clear: Optional, If True, clears the list of errors
    
    Returns:
        A string containing the list of errors if error_message is None,
        otherwise a confirmation message.
    """
    global app_errors

    
    try:
        # If no error message is provided, return the list of errors
        if error_message is None:
            # if app errors is empty
            if not app_errors:
               return "No errors reported. If needed, consider adding in some calls to reportError() in your app code to help with debugging."
            
            # Format the errors as a numbered list
            error_list = "\n".join([f"{i+1}. {err}" for i, err in enumerate(app_errors)])

            if clear:
                app_errors.clear()

            return f"Reported errors:\n{error_list}"
        
        if clear:
            app_errors.clear()

        # Add the error to the list with a timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        app_errors.append(f"[{timestamp}] {error_message}")
        
        # Keep only the last 100 errors to prevent unbounded growth
        if len(app_errors) > 100:
            app_errors = app_errors[-100:]
        
        logger.warning(f"App error reported: {error_message}")
        return f"Error reported: {error_message}"
    
    except Exception as e:
        logger.error(f"Error handling app_error: {e}")
        return f"Failed to process error: {str(e)}"


def main():
    """Entry point for the package when installed via pip."""
    import sys

    # Check command line arguments
    if len(sys.argv) > 1:
        print(f"Unknown argument: {sys.argv[1]}")
        print("No command line arguments are supported")
    else:
        # Normal MCP server mode
        logger.info("Starting MCP server...")
        mcp.run()


if __name__ == "__main__":
    main()