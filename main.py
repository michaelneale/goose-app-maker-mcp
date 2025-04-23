from mcp.server.fastmcp import FastMCP
import os
import subprocess
import logging
import time
import json
import shutil
import http.server
import socketserver
from typing import Dict, Any, List, Optional
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

# Global variable to store the HTTP server instance
http_server = None
server_port = 8000  # Default port

instructions = """
You are a web app generator and server. You help users create and manage web applications
that are stored in the ~/.config/goose/app-maker-apps directory.

You can:
1. Generate new web applications based on user requirements
2. Serve existing web applications locally
3. Modify existing web applications
4. List available web applications
5. Open web applications in the default browser

When generating web apps:
- Create clean, modern, and responsive designs
- Ensure proper HTML, CSS, and JavaScript structure
- Include appropriate documentation
- Use best practices for web development
- Consider accessibility and cross-browser compatibility

Each app is stored in its own directory within ~/.config/goose/app-maker-apps.
"""

mcp = FastMCP("Goose App Maker", instructions=instructions)

def cleanup_old_files(max_age_days=30):
    """
    Clean up temporary files that might have been left behind

    Args:
        max_age_days: Maximum age of files to keep in days
    """
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 3600

    try:
        # We don't auto-delete apps, but we could add cleanup for temp files here
        pass
    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")

# Clean up old files on startup
cleanup_old_files()

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
def create_app(app_name: str, app_type: str, description: str, files: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Create a new web application with the specified files.
    
    Args:
        app_name: Name of the application (will be used as directory name)
        app_type: Type of application (e.g., "static", "react", "vue", etc.)
        description: Brief description of the application
        files: List of files to create, each with "path" and "content" keys
    
    Returns:
        A dictionary containing the result of the operation
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
        
        # Create manifest file
        manifest = {
            "name": app_name,
            "type": app_type,
            "description": description,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "files": [f["path"] for f in files]
        }
        
        with open(os.path.join(app_path, "manifest.json"), 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Create all the files
        for file_info in files:
            file_path = os.path.join(app_path, file_info["path"])
            
            # Create directories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file content
            with open(file_path, 'w') as f:
                f.write(file_info["content"])
        
        return {
            "success": True,
            "app_name": safe_app_name,
            "app_path": app_path,
            "file_count": len(files),
            "message": f"App '{app_name}' created successfully at {app_path}"
        }
    except Exception as e:
        logger.error(f"Error creating app: {e}")
        return {"success": False, "error": f"Failed to create app: {str(e)}"}

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
def serve_app(app_name: str, port: Optional[int] = None) -> Dict[str, Any]:
    """
    Serve an existing web application on a local HTTP server.
    
    Args:
        app_name: Name of the application to serve
        port: Optional port number (default: 8000)
    
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
        
        # Set the port
        if port:
            server_port = port
        
        # Create a custom handler that serves from the app directory
        class AppHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=app_path, **kwargs)
        
        # Start the server in a separate thread
        import threading
        
        def run_server():
            global http_server
            try:
                with socketserver.TCPServer(("", server_port), AppHandler) as server:
                    http_server = server
                    logger.info(f"Serving app '{app_name}' at http://localhost:{server_port}")
                    server.serve_forever()
            except Exception as e:
                logger.error(f"Server error: {e}")
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait a moment for the server to start
        time.sleep(1)
        
        return {
            "success": True,
            "app_name": app_name,
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
        
        # Open the URL in the default browser
        url = f"http://localhost:{server_port}"
        subprocess.run(["open", url], check=True)
        
        return {
            "success": True,
            "app_name": app_name,
            "url": url,
            "message": f"App '{app_name}' opened in browser at {url}"
        }
    except Exception as e:
        logger.error(f"Error opening app: {e}")
        return {"success": False, "error": f"Failed to open app: {str(e)}"}

def test_tools():
    """Test the MCP tools with basic commands."""
    logger.info("Testing Goose App Maker MCP tools")
    
    # Test list_apps
    logger.info("Testing list_apps tool")
    result = list_apps()
    logger.info(f"list_apps result: {result}")
    
    # Create a test app
    logger.info("Testing create_app tool")
    test_files = [
        {
            "path": "index.html",
            "content": """<!DOCTYPE html>
<html>
<head>
    <title>Test App</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Test App</h1>
    <p>This is a test app created by Goose App Maker.</p>
    <script src="script.js"></script>
</body>
</html>"""
        },
        {
            "path": "style.css",
            "content": """body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f0f0f0;
}

h1 {
    color: #333;
}"""
        },
        {
            "path": "script.js",
            "content": """console.log('Test app loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
});"""
        }
    ]
    
    result = create_app("test-app", "static", "A test application", test_files)
    logger.info(f"create_app result: {result}")
    
    # Test serve_app
    logger.info("Testing serve_app tool")
    result = serve_app("test-app")
    logger.info(f"serve_app result: {result}")
    
    # Test open_app
    logger.info("Testing open_app tool")
    result = open_app("test-app")
    logger.info(f"open_app result: {result}")
    
    # Wait a bit before stopping the server
    time.sleep(5)
    
    # Test stop_server
    logger.info("Testing stop_server tool")
    result = stop_server()
    logger.info(f"stop_server result: {result}")


def live_runthrough():
    """Perform a live runthrough that copies the test app files and serves them."""
    logger.info("Starting live runthrough of Goose App Maker")
    
    # Define the source and destination directories
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-app")
    app_name = "goose-demo-app"
    dest_dir = os.path.join(APP_DIR, app_name)
    
    # Check if source directory exists
    if not os.path.exists(src_dir):
        logger.error(f"Source directory '{src_dir}' does not exist")
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
        "type": "static",
        "description": "A demo application with interactive features",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "files": ["index.html", "style.css", "script.js"]
    }
    
    with open(os.path.join(dest_dir, "manifest.json"), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Copy the files
    try:
        for file_name in ["index.html", "style.css", "script.js"]:
            src_file = os.path.join(src_dir, file_name)
            dest_file = os.path.join(dest_dir, file_name)
            
            if os.path.exists(src_file):
                logger.info(f"Copying {file_name} to {dest_file}")
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
                logger.info("Demo app opened successfully")
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
        if sys.argv[1] == "--test":
            test_tools()
        elif sys.argv[1] == "--demo" or sys.argv[1] == "--live":
            live_runthrough()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Available options: --test, --demo/--live")
    else:
        # Normal MCP server mode
        logger.info("Starting MCP server...")
        mcp.run()


if __name__ == "__main__":
    main()
