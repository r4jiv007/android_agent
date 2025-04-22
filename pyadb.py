import shutil
import subprocess
from platform import system
import time
from sys import stdout
from PIL import Image
from typing import List, Optional, Tuple

from PIL.ImagePalette import raw

function_declarations = [
    {
        "name": "check_if_adb_installed",
        "description": "Checks if ADB is installed and available in the system path. Returns the path to ADB or an error.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "make_adb_command",
        "description": "Creates a complete ADB command string by combining the ADB executable path and the command.",
        "parameters": {
            "type": "object",
            "properties": {
                "adb": {
                    "type": "string",
                    "description": "Path to the ADB executable"
                },
                "command": {
                    "type": "string",
                    "description": "The ADB command to execute"
                }
            },
            "required": ["adb", "command"]
        }
    },
    {
        "name": "run_command",
        "description": "Executes an ADB command and returns the result as a CompletedProcess object or an error message.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The ADB command to execute (without the ADB path)"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "list_android_devices",
        "description": "Lists all connected Android devices with their details and status. Returns a list of device objects or an error.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "parse_device_list",
        "description": "Parses the raw output from 'adb devices' command and extracts device information including status, ID, and details.",
        "parameters": {
            "type": "object",
            "properties": {
                "adb_path": {
                    "type": "string",
                    "description": "Path to the ADB executable"
                },
                "raw_device_list": {
                    "type": "string",
                    "description": "Raw output from 'adb devices' command"
                }
            },
            "required": ["adb_path", "raw_device_list"]
        }
    },
    {
        "name": "is_emulator",
        "description": "Determines if a device is an emulator or a physical device by checking device ID and system properties.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "The device identifier"
                },
                "adb_path": {
                    "type": "string",
                    "description": "Path to the ADB executable"
                }
            },
            "required": ["device_id", "adb_path"]
        }
    },
    {
        "name": "get_device_details",
        "description": "Gets detailed information about a specific device including model, Android version, and serial number.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "The device identifier"
                },
                "adb_path": {
                    "type": "string",
                    "description": "Path to the ADB executable"
                }
            },
            "required": ["device_id", "adb_path"]
        }
    },
    {
        "name": "take_screenshot",
        "description": "Takes a screenshot of the connected Android device, saves it as a PNG file with timestamp, and returns the raw PNG data.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "The device identifier. If None, uses the default device."
                }
            },
            "required": []
        }
    },
    {
        "name": "tap",
        "description": "Taps at the specified coordinates on the device screen and returns operation result details.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer",
                    "description": "X coordinate"
                },
                "y": {
                    "type": "integer",
                    "description": "Y coordinate"
                }
            },
            "required": ["x", "y"]
        }
    },
    {
        "name": "swipe",
        "description": "Swipes from one point to another on the device screen with configurable duration and returns operation result details.",
        "parameters": {
            "type": "object",
            "properties": {
                "x1": {
                    "type": "integer",
                    "description": "Starting X coordinate"
                },
                "y1": {
                    "type": "integer",
                    "description": "Starting Y coordinate"
                },
                "x2": {
                    "type": "integer",
                    "description": "Ending X coordinate"
                },
                "y2": {
                    "type": "integer",
                    "description": "Ending Y coordinate"
                },
                "duration": {
                    "type": "integer",
                    "description": "Swipe duration in milliseconds. Defaults to 300."
                }
            },
            "required": ["x1", "y1", "x2", "y2"]
        }
    },
    {
        "name": "input_text",
        "description": "Inputs text on the device with special character handling and returns operation result details.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to input (spaces will be converted to %s and single quotes will be escaped)"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "press_key",
        "description": "Presses a key on the device by sending a keyevent and returns operation result details.",
        "parameters": {
            "type": "object",
            "properties": {
                "keycode": {
                    "type": "string",
                    "description": "Key code (e.g., 'HOME', 'BACK'). Will be prefixed with 'KEYCODE_' if not already present."
                }
            },
            "required": ["keycode"]
        }
    },
    {
        "name": "launch_app",
        "description": "Launches an application by package name using either activity resolution or monkey tool and returns detailed operation result.",
        "parameters": {
            "type": "object",
            "properties": {
                "package_name": {
                    "type": "string",
                    "description": "Package name of the app to launch"
                }
            },
            "required": ["package_name"]
        }
    },
    {
        "name": "get_installed_packages",
        "description": "Gets a list of all installed packages on the device by parsing the output of 'pm list packages'.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]
 
class PyAdb:
    def check_if_adb_installed(self):
        """
        Checks if ADB is installed and available in the system path.

        Returns:
            tuple: (path_to_adb, error_message)
                - path_to_adb (str or None): Path to the ADB executable if found
                - error_message (str or None): Error message if ADB is not found
        """
        if shutil.which('adb') is not None:
            return shutil.which('adb'), None
        else:
            return None, "Error can't locate adb"

    def make_adb_command(self, adb, command):
        """
        Creates a complete ADB command string by combining the ADB path and the command.

        Args:
            adb (str): Path to the ADB executable
            command (str): The ADB command to execute

        Returns:
            str: The complete ADB command
        """
        return f"{adb} {command}"

    def run_command(self, command):
        """
        Executes an ADB command and returns the result.

        Args:
            command (str): The ADB command to execute (without the ADB path)

        Returns:
            tuple: (result, error)
                - result (subprocess.CompletedProcess or None): Result of command execution
                - error (str or None): Error message if ADB is not installed
        """
        path, error = self.check_if_adb_installed()

        if error is not None:
            return None, error

        task = self.make_adb_command(path, command)
        print(task)
        result = subprocess.run(task, shell=True, capture_output=True, text=True)
        return result, None

    def list_android_devices(self):
        """
        Lists all connected Android devices.

        Returns:
            tuple: (devices_list, error)
                - devices_list (list or None): List of connected devices with their details
                - error (str or None): Error message if ADB is not installed or fails
        """
        path, error = self.check_if_adb_installed()
        if error is not None:
            return None, error
        else:
            command = self.make_adb_command(path, "devices")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                return None, result.stderr
            else:
                return self.parse_device_list(path, result.stdout)

    def parse_device_list(self, adb_path, raw_device_list):
        """
        Parses the raw output from 'adb devices' command and extracts device information.

        Args:
            adb_path (str): Path to the ADB executable
            raw_device_list (str): Raw output from 'adb devices' command

        Returns:
            list: List of dictionaries containing device information with keys:
                - status: Device connection status (e.g., 'device', 'offline')
                - id: Device identifier
                - is_emulator: Boolean indicating if the device is an emulator
                - detail: Tuple containing (device_details, error)
        """
        device_map = []

        # Split by lines and skip the first line (header line "List of devices attached")
        device_lines = raw_device_list.strip().split('\n')
        if len(device_lines) > 1:
            device_lines = device_lines[1:]  # Skip the header

        for device_line in device_lines:
            if device_line.strip():  # Skip empty lines
                parts = device_line.strip().split('\t')
                if len(parts) >= 2:
                    device_id = parts[0]
                    status = parts[1]
                    detail = self.get_device_details(device_id, adb_path)
                    # Create a device entry with basic info
                    device_map.append({
                        'status': status,
                        'id': device_id,
                        'is_emulator': self.is_emulator(device_id, adb_path),
                        'detail': detail
                    })

        return device_map

    def is_emulator(self, device_id, adb_path):
        """
        Determines if a device is an emulator or a physical device.

        Args:
            device_id (str): The device identifier
            adb_path (str): Path to the ADB executable

        Returns:
            bool: True if the device is an emulator, False if it's a physical device
        """
        # Method 1: Check the device ID format
        if device_id.startswith('emulator-') or device_id.startswith('localhost:'):
            return True

        # Method 2: Check specific properties that identify emulators
        indicators = [
            # Check the fingerprint (contains 'generic' in emulators)
            ("ro.build.fingerprint", "generic", "contains"),
            # Check hardware model
            ("ro.hardware", "ranchu", "equals"),  # ranchu is the Android emulator hardware name
            ("ro.hardware", "goldfish", "equals"),  # older emulator identifier
            # Check product name
            ("ro.product.model", "Android SDK built for", "contains"),
            # Check manufacturer
            ("ro.product.manufacturer", "Google", "equals"),
            # Check if qemu.hw.mainkeys exists (only exists on emulators)
            ("qemu.hw.mainkeys", "", "exists")
        ]

        for prop, value, check_type in indicators:
            cmd = self.make_adb_command(adb_path, f"-s {device_id} shell getprop {prop}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                output = result.stdout.strip()

                if check_type == "contains" and value in output:
                    return True
                elif check_type == "equals" and output == value:
                    return True
                elif check_type == "exists" and output:
                    return True

        # If none of the indicators match, it's likely a physical device
        return False

    def get_device_details(self, device_id, adb_path):
        """
        Gets detailed information about a specific device.

        Args:
            device_id (str): The device identifier
            adb_path (str): Path to the ADB executable

        Returns:
            tuple: (details, error)
                - details (dict or None): Dictionary containing device details (model, android_version, serial) if successful
                - error (str or None): Error message if any property retrieval fails
        """
        details = {}

        # Get device model
        cmd = self.make_adb_command(adb_path, f"-s {device_id} shell getprop ro.product.model")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            details['model'] = result.stdout.strip()
        else:
            return None, result.stderr

        # Get Android version
        cmd = self.make_adb_command(adb_path, f"-s {device_id} shell getprop ro.build.version.release")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            details['android_version'] = result.stdout.strip()
        else:
            return None, result.stderr

        # Get device serial number
        cmd = self.make_adb_command(adb_path, f"-s {device_id} shell getprop ro.serialno")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            details['serial'] = result.stdout.strip()
        else:
            return None, result.stderr

        return details, None

    def take_screenshot(self, device_id=None):
        """
        Takes a screenshot of the connected Android device, saves it as a PNG file with timestamp, and returns the raw PNG data.

        Args:
            device_id (str, optional): The device identifier. If None, uses the default device.

        Returns:
            tuple: (raw_data, error)
                - raw_data (bytes or None): Raw PNG data of the screenshot if successful
                - error (str or None): Error message if the operation fails
        """
        path, error = self.check_if_adb_installed()
        if error is not None:
            return None, error

        device_param = f"-s {device_id} " if device_id else ""
        filename = f"{time.time()}_screen.png"

        # Capture screenshot data using ADB screencap command with -p flag (PNG format)
        command = self.make_adb_command(path, f"{device_param}shell screencap -p")
        screen_cap_result = subprocess.run(command, shell=True, capture_output=True)
        
        if screen_cap_result.returncode != 0:
            return None, "Failed to capture screenshot"
        
        try:
            # Get the raw data
            raw_data = screen_cap_result.stdout
            
            # Save it to a file (optional)
            with open(filename, 'wb') as f:
                f.write(raw_data)
            
            return raw_data, None
        except Exception as e:
            return None, f"Error processing screenshot data: {str(e)}"

    def tap(self, x: int, y: int) -> dict:
        """
        Taps at the specified coordinates on the device screen.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            dict: Result of the tap operation including:
                - success (bool): Whether the command was successful
                - return_code (int): The return code of the command
                - stdout (str): Standard output if any
                - stderr (str): Standard error if any
                - command (str): The command that was executed
        """
        command = f"shell input tap {x} {y}"
        result, error = self.run_command(command)
        
        if error:
            return {
                "success": False,
                "error": error,
                "command": command
            }
        
        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command
        }

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> dict:
        """
        Swipes from one point to another on the device screen.

        Args:
            x1 (int): Starting X coordinate
            y1 (int): Starting Y coordinate
            x2 (int): Ending X coordinate
            y2 (int): Ending Y coordinate
            duration (int, optional): Swipe duration in milliseconds. Defaults to 300.
            
        Returns:
            dict: Result of the swipe operation including:
                - success (bool): Whether the command was successful
                - return_code (int): The return code of the command
                - stdout (str): Standard output if any
                - stderr (str): Standard error if any
                - command (str): The command that was executed
        """
        command = f"shell input swipe {x1} {y1} {x2} {y2} {duration}"
        result, error = self.run_command(command)
        
        if error:
            return {
                "success": False,
                "error": error,
                "command": command
            }
        
        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command
        }

    def input_text(self, text: str) -> dict:
        """
        Inputs text on the device.

        Args:
            text (str): Text to input
            
        Returns:
            dict: Result of the text input operation including:
                - success (bool): Whether the command was successful
                - return_code (int): The return code of the command
                - stdout (str): Standard output if any
                - stderr (str): Standard error if any
                - command (str): The command that was executed
        """
        # Escape special characters for shell
        text = text.replace("'", "\\'").replace(" ", "%s")
        command = f"shell input text '{text}'"
        result, error = self.run_command(command)
        
        if error:
            return {
                "success": False,
                "error": error,
                "command": command
            }
        
        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command
        }

    def press_key(self, keycode: str) -> dict:
        """
        Presses a key on the device.

        Args:
            keycode (str): Key code (e.g., 'HOME', 'BACK')
                Will be prefixed with 'KEYCODE_' if not already present

        Returns:
            dict: Result of the key press operation including:
                - success (bool): Whether the command was successful
                - return_code (int): The return code of the command
                - stdout (str): Standard output if any
                - stderr (str): Standard error if any
                - command (str): The command that was executed
        """
        if not keycode.startswith("KEYCODE_"):
            keycode = f"KEYCODE_{keycode}"

        command = f"shell input keyevent {keycode}"
        result, error = self.run_command(command)
        
        if error:
            return {
                "success": False,
                "error": error,
                "command": command
            }
        
        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command
        }

    def launch_app(self, package_name: str) -> dict:
        """
        Launches an application by package name.

        Args:
            package_name (str): Package name of the app to launch
            
        Returns:
            dict: Result of the app launch operation including:
                - success (bool): Whether the command was successful
                - return_code (int): The return code of the command
                - stdout (str): Standard output if any
                - stderr (str): Standard error if any
                - command (str): The command that was executed
        """
        # Get launcher activity for the package
        resolve_cmd = f"shell cmd package resolve-activity --brief {package_name}"
        result, error = self.run_command(resolve_cmd)
        
        if error:
            return {
                "success": False,
                "error": error,
                "command": resolve_cmd
            }

        if result.returncode != 0 or result.stderr or "No activity found" in result.stdout:
            # Try direct method if activity resolution fails
            monkey_cmd = f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
            monkey_result, monkey_error = self.run_command(monkey_cmd)
            
            if monkey_error:
                return {
                    "success": False,
                    "error": monkey_error,
                    "command": monkey_cmd
                }
            
            return {
                "success": monkey_result.returncode == 0,
                "return_code": monkey_result.returncode,
                "stdout": monkey_result.stdout,
                "stderr": monkey_result.stderr,
                "command": monkey_cmd,
                "method": "monkey"
            }
        else:
            # Extract and launch the main activity
            stdout = result.stdout.strip()
            activity = stdout.splitlines()[1].strip()
            start_cmd = f"shell am start -n {activity}"
            start_result, start_error = self.run_command(start_cmd)
            
            if start_error:
                return {
                    "success": False,
                    "error": start_error,
                    "command": start_cmd
                }
            
            return {
                "success": start_result.returncode == 0,
                "return_code": start_result.returncode,
                "stdout": start_result.stdout,
                "stderr": start_result.stderr,
                "command": start_cmd,
                "method": "am start",
                "activity": activity
            }

    def get_installed_packages(self) -> List[str]:
        """
        Gets a list of installed packages on the device.

        Returns:
            tuple: (packages, error)
                - packages (List[str] or None): List of package names if successful
                - error (str or None): Error message if the operation fails
        """
        stdout, error = self.run_command("shell pm list packages")
        if error:
            return None, error
        packages = []

        for line in stdout.splitlines():
            if line.startswith("package:"):
                package = line[8:].strip()  # Remove 'package:' prefix
                packages.append(package)

        return packages, None