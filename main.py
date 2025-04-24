from mcp.server.fastmcp import FastMCP
import os
import subprocess
import logging
import time
import json
import shutil
import http.server
import socketserver
from typing import Dict, Any, Optional
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

instructions = """
You are an expert html5/CSS/js web app author for casual "apps" for goose.

You can also serve up apps via a built in server. 
You help users create and manage web applications that are stored in the ~/.config/goose/app-maker-apps directory.

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
- You can use the goose_api.js when data needs to be dynamic
- Care is needed when using other apis as they may not always be available, and credentials may be required (so consider using goose_api.js)
- Open the app as it is built with the default browser to show the user, and invite feedback
- Use other tools as available to assist in building the app (such as screenshot for visual review)
- Other tools can be used via the goose_api.js library in the app as needed (it will return textual data so can be prompted to format it appropriately, markdown works well, simple lists etc)

Each app is stored in its own directory within ~/.config/goose/app-maker-apps.

Once an app is created, you can modify or replace contents of its files using tools available. Typically there is an index.html, style.css, and script.js file (and the goose_api.js helper) - but you don't have to stick to this structure if you know better.

The directory ~/.config/goose/app-maker-apps/[app-name]/ is where the app is stored.

Resources:
- The resources directory is located at: {resources_dir} which has utilities and examples you can refer to.
- For example apps and templates, refer to the examples in the [README.md]({readme_path})
- For apps requiring dynamic functionality or access to data sources/services, include [goose_api.js]({goose_api_path}) in your app
  - This script provides methods to communicate with the Goose API
  - When served, environment variables like $GOOSE_PORT and $GOOSE_SERVER__SECRET_KEY are automatically replaced with actual values
  - include that with app files, placed next to them
  - When using sendGooseRequest(message) - the message should clearly specify the desired format (list, markdown, json - default will return just a text value which is also useful)

  Some of the tools available:

    create_app - use this when starting new
    list_apps - find existing apps 
    serve_app - serve an app locally
    open_app - open an app in a browser (macos)
    update_app_file - update a file in an app
    view_app_file - view a file in an app


"""

# Format the instructions with dynamic paths
instructions = instructions.format(
    resources_dir=RESOURCES_DIR,
    readme_path=README_PATH,
    goose_api_path=GOOSE_API_PATH
)

mcp = FastMCP("Goose App Maker", instructions=instructions)


@mcp.tool()
def publish_app(app_name: str) -> Dict[str, Any]:
    """
    Publish an app to the web. This is a placeholder function.
    
    Args:
        app_name: Name of the application to publish
    """

    # TODO: this could zip up the app dir
    # still working on how to share this

    return
            



@mcp.tool()
def list_apps() -> Dict[str, Any]:
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
                
                # Check if there's a manifest.json file
                manifest_path = app_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                            app_info["manifest"] = manifest
                    except json.JSONDecodeError:
                        app_info["manifest_error"] = "Invalid manifest.json file"
                
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
def update_app_file(app_name: str, file_path: str, content: str) -> Dict[str, Any]:
    """
    Update or create a file in an existing web application.
    
    Args:
        app_name: Name of the application
        file_path: Path to the file within the app directory
        content: New content for the file
    
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
        
        # Create the full file path
        full_file_path = os.path.join(app_path, file_path)
        
        # Create directories if needed
        os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
        
        # Write file content
        with open(full_file_path, 'w') as f:
            f.write(content)
        
        # Update manifest if it exists
        manifest_path = os.path.join(app_path, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                if "files" not in manifest:
                    manifest["files"] = []
                
                if file_path not in manifest["files"]:
                    manifest["files"].append(file_path)
                    manifest["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    with open(manifest_path, 'w') as f:
                        json.dump(manifest, f, indent=2)
            except Exception as e:
                logger.warning(f"Error updating manifest: {e}")
        
        return {
            "success": True,
            "app_name": app_name,
            "file_path": file_path,
            "full_path": full_file_path,
            "message": f"File '{file_path}' updated successfully in app '{app_name}'"
        }
    except Exception as e:
        logger.error(f"Error updating app file: {e}")
        return {"success": False, "error": f"Failed to update file: {str(e)}"}

@mcp.tool()
def view_app_file(app_name: str, file_path: str) -> Dict[str, Any]:
    """
    View the content of a file in an existing web application.
    
    Args:
        app_name: Name of the application
        file_path: Path to the file within the app directory
    
    Returns:
        A dictionary containing the content of the file
    """
    try:
        # Find the app directory
        app_path = os.path.join(APP_DIR, app_name)
        if not os.path.exists(app_path):
            return {
                "success": False, 
                "error": f"App '{app_name}' not found at {app_path}"
            }
        
        # Create the full file path
        full_file_path = os.path.join(app_path, file_path)
        
        if not os.path.exists(full_file_path):
            return {
                "success": False, 
                "error": f"File '{file_path}' not found in app '{app_name}'"
            }
        
        # Read file content
        with open(full_file_path, 'r') as f:
            content = f.read()
        
        return {
            "success": True,
            "app_name": app_name,
            "file_path": file_path,
            "content": content
        }
    except Exception as e:
        logger.error(f"Error viewing app file: {e}")
        return {"success": False, "error": f"Failed to view file: {str(e)}"}

@mcp.tool()
def delete_app(app_name: str) -> Dict[str, Any]:
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
def create_app(app_name: str, description: str = "") -> Dict[str, Any]:
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

    """
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
        
        with open(os.path.join(app_path, "manifest.json"), 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return {
            "success": True,
            "app_name": safe_app_name,
            "app_path": app_path,
            "message": f"App '{app_name}' created successfully at {app_path}"
        }
    except Exception as e:
        logger.error(f"Error creating app: {e}")
        return {"success": False, "error": f"Failed to create app: {str(e)}"}

@mcp.tool()
def serve_app(app_name: str) -> Dict[str, Any]:
    """
    Serve an existing web application on a local HTTP server.
    The server will automatically find an available port.
    
    Args:
        app_name: Name of the application to serve
    
    Returns:
        A dictionary containing the result of the operation
    """
    global http_server, server_port
    
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
def stop_server() -> Dict[str, Any]:
    """
    Stop the currently running HTTP server.
    
    Returns:
        A dictionary containing the result of the operation
    """
    global http_server
    
    try:
        if http_server:
            logger.info("Stopping HTTP server")
            http_server.shutdown()
            http_server.server_close()
            http_server = None
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
def open_app(app_name: str) -> Dict[str, Any]:
    """
    Open an app in the default web browser. If the app is not currently being served,
    it will be served first.
    
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
            serve_result = serve_app(app_name)
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
def refresh_app() -> Dict[str, Any]:
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


def live_runthrough():
    """Perform a live runthrough that copies the test app files and serves them."""
    logger.info("Starting live runthrough of Goose App Maker")
    
    # Define the source directories
    test_app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/kitchen-sink")
    resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    
    # Define the destination
    app_name = "goose-demo-app"
    dest_dir = os.path.join(APP_DIR, app_name)
    
    # Check if source directories exist
    if not os.path.exists(test_app_dir):
        logger.error(f"Test app directory '{test_app_dir}' does not exist")
        return False
    
    if not os.path.exists(resources_dir):
        logger.error(f"Resources directory '{resources_dir}' does not exist")
        return False
    
    # Delete the destination directory if it exists
    if os.path.exists(dest_dir):
        logger.info(f"Removing existing app at '{dest_dir}'")
        shutil.rmtree(dest_dir)
    
    # Create the destination directory
    os.makedirs(dest_dir, exist_ok=True)
    
    # Create the manifest file
    manifest = {
        "name": "Goose Demo App",
        "description": "A demo application with interactive features",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "files": ["index.html", "style.css", "script.js", "goose_api.js"]
    }
    
    with open(os.path.join(dest_dir, "manifest.json"), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Copy the files
    try:
        # Copy test app files (except goose_api.js which will come from resources)
        for file_name in ["index.html", "style.css", "script.js", "goose_api.js"]:
            src_file = os.path.join(test_app_dir, file_name)
            dest_file = os.path.join(dest_dir, file_name)
            
            if os.path.exists(src_file):
                logger.info(f"Copying {file_name} from {src_file} to {dest_file}")
                shutil.copy2(src_file, dest_file)
            else:
                logger.error(f"Source file '{src_file}' does not exist")
                return False
                
        logger.info(f"Successfully copied all files to {dest_dir}")
        
        # Serve the app
        logger.info("Serving the demo app")
        serve_result = serve_app(app_name)
        
        if serve_result["success"]:
            # Open the app in the browser
            logger.info("Opening the demo app in browser")
            open_result = open_app(app_name)
            
            if open_result["success"]:
                logger.info(f"Demo app opened successfully at {serve_result['url']}")
                logger.info("Press Ctrl+C to stop the server and exit")
                
                # Keep the server running until interrupted
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Stopping server due to keyboard interrupt")
                    stop_server()
            else:
                logger.error(f"Failed to open app: {open_result.get('error', 'Unknown error')}")
                return False
        else:
            logger.error(f"Failed to serve app: {serve_result.get('error', 'Unknown error')}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error during live runthrough: {e}")
        return False


def main():
    """Entry point for the package when installed via pip."""
    import sys

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo" or sys.argv[1] == "--live":
            live_runthrough()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Available options: --demo/--live")
    else:
        # Normal MCP server mode
        logger.info("Starting MCP server...")
        mcp.run()


if __name__ == "__main__":
    main()