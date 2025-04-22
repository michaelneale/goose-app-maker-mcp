from mcp.server.fastmcp import FastMCP
import os
import subprocess
import logging
import tempfile
import time
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("Starting Personal Shopper MCP server...")

instructions = """
You are a helpful personal shopping assitant. You have access to various tools to help the user do product research, establish preferences and even purchase (or add to shopping carts of various kinds). You also have access to personal information, prefences, schedules and messages and more. 

IMPORTANT: Always reply very very briefly and to the point as your results are only viewed on mobile screen

SHOW YOUR WORKING: When operating, always use update_status tool to provide brief updates on what you're currently doing or planning.

Tools: 
- you have afterpay tools, list_payments is main recommended one if you want to establish buying preferences, or a profile when needed, a good idea to do this up front
- use shop_helper for directing the personal device agent to take action or return results.
- use take_screenshot if part of that action could do with a visual to return to the user (eg a product or screen, or when asked)


Scenarios: 

* you can support scenarios like planning a party, which means thinking up ideas, searching for products, food, delivery, checking calendars, messages from people, emails, finding a local venue, local vendors
    - do a search for ideas, look at calendar for times, consider who is invited, what food could be delivered, and suggestion options available
* buying new tyres (check calendar, see if you can work out what sort of car the user has, or ask) 
    - serach for local fitting shops
    - do a product search using any ecom apps or web search for prices
* office meetup and food ordering
    - find local catering and prices (ask it to do a search and open in maps)
* trip to europe
    - look up booking sites for hotels, apps for hotels or flights, consider what items may want to be purchased
* find me a paint set
    - look up apps like amazon for painting products that are available within a week of delivery, that have good reviews, suggest a few
    - add items to amazon cart if asked
* research lock box for keys
    - search web, and amazon and other apps for key lock boxes
    - note reviews, scroll for several products, collect prices and note reviews (more than 4 star, more than 100 reviews for example)
    - cross check with web search, not just app search alone
    - add one to shopping cart that seems best, factoring in delivery time

when using shop_helper, give clear instructions, it may be to open a specific app like amazon, afterpay, ebay etc and interact
you can ask it to scroll more, click in to details, read reviews, add to shopping carts. 
You can also try general instructions, but it may not always work so you can try again with other combinations of specifics several times if needed. 
It also has access to personal information, calendars, notes, messages, emails as needed.


Getting started
ALWAYS:
* check what apps are availble
* build a personal shopping profile using both shopper_profile tool and list_payments tool (summarize findings)
* after the above: commence tasks, you can ask user later for preferences as you go.
* check that the products being reviewed/purchased do make sense for the original task request

be creative, and ALWAYS report back your status regularly as things may go on (especially when researching, and let it know what stage you are up to). 
You may need to return to user - and they will let you know if it is time to continue with it or not.
Important: don't overdo it with product research, be efficient and get to the point 

Finally, 
1) if you are adding to a cart or purchasing, check that the right things are in the cart and it makes sense based on the original request
2) use the take_screenshot to show if there is something visual to present (it will automatically be shown)
3) ALWAYS use write_result to write a very short markdown summary of results and actions to be shown to the user on a mobile screen.

The Personal Shopper MCP provides tools to interact with a mobile smart agent, with many shopping apps and personal utilities and information available.
It allows you to:
1. Execute shopping/personal instructions on the device  and get an answer in text
2. Take screenshots of the device screen and save them locally to present to the user of apps/products
3. other utilities to help inform you
"""

mcp = FastMCP("Personal Shopper", instructions=instructions)

# Create a temporary directory for storing screenshots
TEMP_DIR = os.path.join(tempfile.gettempdir(), "personal_shopper")
os.makedirs(TEMP_DIR, exist_ok=True)
logger.info(f"Using temporary directory: {TEMP_DIR}")


def cleanup_old_files(max_age_hours=24):
    """
    Clean up old temporary files that might have been left behind

    Args:
        max_age_hours: Maximum age of files to keep in hours
    """
    import time

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    try:
        for file_path in Path(TEMP_DIR).glob("*.png"):
            if current_time - file_path.stat().st_mtime > max_age_seconds:
                logger.info(f"Cleaning up old file: {file_path}")
                file_path.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")


# Clean up old files on startup
cleanup_old_files()


def check_adb_connection():
    """Check if an Android device is connected via ADB."""
    try:
        result = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, check=True
        )
        # Check if any device is listed (excluding the "List of devices attached" line)
        lines = result.stdout.strip().split("\n")
        if len(lines) <= 1:
            return False, "No devices connected via ADB"
        return True, "ADB device connected"
    except subprocess.CalledProcessError as e:
        return False, f"ADB error: {e}"
    except FileNotFoundError:
        return False, "ADB not found in PATH"

@mcp.tool()
def shopper_profile() -> Dict[str, Any]:
    """Look at history to see help make a personal shopper profile."""
    return shop_helper("can you summarize my shopper profile in a paragraph")


@mcp.tool()
def what_apps() -> Dict[str, Any]:
    """List the available apps on the personal device and what they can be used for."""
    return shop_helper("what apps do you have available?")

@mcp.tool()
def web_search(topic: str) -> Dict[str, Any]:
    """Use this to do a web search
        Args: 
            what to search for
        Returns:
            The result of the search
    """
    return shop_helper("Open chrome and do a web search, scroll down a bit to ensure you can see a set of results and report back, when finished, make sure you go back so browser is clean state. Topic: " + topic)

@mcp.tool()
def shop_helper(command: str) -> Dict[str, Any]:
    """
    Execute an instruction on the personal device (just like a person would ask an assistant to do), and return the result.
    This is for interacting with another smart agent, which has access to personal information and shopping apps.
    Use this when you want to interact with an app, web search or access personal information.
    You can use this to add items to shopping carts, browse, scroll around, click in and inspect.     
    if you don't see what you need, repeat the request and ask it to scroll up a few screens to see a button or the fill listing or to find an element that should be there
    Many apps are available and are personalised to the user already, including calendars, email, messaging and more.
        
    Args:
        command: The instructions to follow
        
    Returns:
        A dictionary containing the success and result of the command execution
    """
    # Check ADB connection first
    adb_connected, message = check_adb_connection()
    if not adb_connected:
        return {"success": False, "error": message}
    
    try:
        # Clear any previous result
        subprocess.run(
            ["adb", "shell", "rm", "-rf", "/storage/emulated/0/Android/data/xyz.block.gosling/files/latest_command_result.txt"],
            check=True,
            capture_output=True
        )
        escaped_command = "'" + command.replace("'", "'\\''") + "'"
        # Send the command to the app
        subprocess.run(
            ["adb", "shell", "am", "start", "-a", "xyz.block.gosling.EXECUTE_COMMAND", 
             "-n", "xyz.block.gosling/.features.agent.DebugActivity", 
             "--es", "command", escaped_command],
            check=True,
            capture_output=True
        )
        
        # Wait for the result file to be created
        max_wait_seconds = 90
        wait_time = 0
        result_file_exists = False
        
        while wait_time < max_wait_seconds:
            check_result = subprocess.run(
                ["adb", "shell", "[ -f /storage/emulated/0/Android/data/xyz.block.gosling/files/latest_command_result.txt ] && echo 'exists'"],
                capture_output=True,
                text=True
            )
            
            if "exists" in check_result.stdout:
                result_file_exists = True
                break
                
            time.sleep(1)
            wait_time += 1
        
        if not result_file_exists:
            return {"success": False, "error": f"Command timed out after {max_wait_seconds} seconds"}
        
        # Get the result
        result = subprocess.run(
            ["adb", "shell", "cat", "/storage/emulated/0/Android/data/xyz.block.gosling/files/latest_command_result.txt"],
            capture_output=True,
            text=True,
            check=True
        )
        
        return {"success": True, "result": result.stdout}
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing shop command: {e}")
        return {"success": False, "error": f"Command execution failed: {e}", "stderr": e.stderr}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


@mcp.tool()
def update_status(status: str) -> Dict[str, Any]:
    """
    Update the status for the user as this is a long running task, being a personal shoper.
    Use this to provide brief updates on what you're currently doing or planning.
    
    Args:
        status: The status message to write to the file, no more than 5 words
        
    """
    try:
        with open("/tmp/goose-status", "w") as f:
            f.write(status)
        logger.info(f"Status updated: {status}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return {"success": False, "error": f"Failed to update status: {str(e)}"}
    
@mcp.tool()
def write_result(result: str) -> Dict[str, Any]:
    """
    Write the results of the actions and output to a summary markdown file for presentation. 
    Should be very brief for mobile presentation.
    Args:
        markdown content
        
    """
    try:
        with open("/tmp/result.md", "w") as f:
            f.write(result)
        logger.info(f"result written: {result}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return {"success": False, "error": f"Failed to update status: {str(e)}"}



@mcp.tool()
def take_screenshot() -> Dict[str, Any]:
    """
    Take a screenshot of the personal device, use this when you want to show the result of a product search or app interaction. 
    Only when there is something notable to present or when asked to show.
    
    The screenshot is always saved to '/tmp/latest_command_result.png' in the current directory.
                    
    Returns:
        A dictionary containing the path to the saved screenshot
    """
    # Check ADB connection first
    adb_connected, message = check_adb_connection()
    if not adb_connected:
        return {"success": False, "error": message}
    
    try:
        # Always save to latest_command_result.png in the current directory
        output_path = "/tmp/latest_command_result.png"
        
        # Take the screenshot on the device
        subprocess.run(
            ["adb", "shell", "screencap", "-p", "/sdcard/latest_command_result.png"],
            check=True,
            capture_output=True
        )
        
        # Pull the screenshot to the local machine
        subprocess.run(
            ["adb", "pull", "/sdcard/latest_command_result.png", output_path],
            check=True,
            capture_output=True
        )
        
        # Get the absolute path for clearer reporting
        abs_path = os.path.abspath(output_path)
        
        return {
            "success": True, 
            "screenshot_path": abs_path,
            "message": f"Screenshot saved to {abs_path}"
        }
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error taking screenshot: {e}")
        return {"success": False, "error": f"Screenshot failed: {e}", "stderr": e.stderr}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def test_tools():
    """Test the MCP tools with basic commands."""
    logger.info("Testing Personal Shopper MCP tools")
    
    # Test ADB connection
    adb_connected, message = check_adb_connection()
    logger.info(f"ADB connection: {message}")
    
    if not adb_connected:
        logger.error("Cannot test tools without ADB connection")
        return
    
    # Test shop_helper
    logger.info("Testing shop_helper tool with 'help' command")
    result = shop_helper("help")
    logger.info(f"shop_helper result: {result}")
    
    # Test update_status
    logger.info("Testing update_status tool")
    result = update_status("Testing status update")
    logger.info(f"update_status result: {result}")
    
    # Test take_screenshot
    logger.info("Testing take_screenshot tool")
    result = take_screenshot()
    logger.info(f"take_screenshot result: {result}")


def main():
    """Entry point for the package when installed via pip."""
    import sys

    # Check if we should run in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_tools()
    else:
        # Normal MCP server mode
        logger.info("Starting MCP server...")
        mcp.run()


if __name__ == "__main__":
    main()