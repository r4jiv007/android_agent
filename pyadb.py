import shutil
import subprocess
from platform import system
import time
from sys import stdout
from typing import List, Optional, Tuple


class PyAdb:
    def check_if_adb_installed(self):
        if shutil.which('adb') is not None:
            return shutil.which('adb'), None
        else:
            return None, "Error can't locate adb"

    def make_adb_command(self, adb, command):
        return f"{adb} {command}"

    def run_command(self, command):
        path, error = self.check_if_adb_installed()

        if error is not None:
            return None,error

        task = self.make_adb_command(path, command)
        print(task)
        result = subprocess.run(task, shell=True, capture_output=True, text=True)
        return result,None

    def list_android_devices(self):
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
        Determine if the device is an emulator or a physical device.
        Returns True if it's an emulator, False if it's a physical device.
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
        details = {}

        # Get device model
        cmd = self.make_adb_command(adb_path, f"-s {device_id} shell getprop ro.product.model")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            details['model'] = result.stdout.strip()

        # Get Android version
        cmd = self.make_adb_command(adb_path, f"-s {device_id} shell getprop ro.build.version.release")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            details['android_version'] = result.stdout.strip()

        # Get device serial number
        cmd = self.make_adb_command(adb_path, f"-s {device_id} shell getprop ro.serialno")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            details['serial'] = result.stdout.strip()

        return details

    # def get_all_devices_with_details():
    #     raw_list, error = list_android_devices()
    #     if error is not None:
    #         return None, error
    #
    #     device_map = parse_device_list(raw_list)
    #     adb_path, _ = check_if_adb_installed()
    #
    #     # Enrich each device with additional details
    #     for device in device_map:
    #         if device['status'] == 'device':  # Only get details for connected devices
    #             details = get_device_details(device['id'], adb_path)
    #             device_map[device_id].update(details)
    #
    #     return device_map, None

    def take_screenshot(self, device_id=None):
        path, error = self.check_if_adb_installed()
        if error is not None:
            return None, error

        device_param = f"-s {device_id} " if device_id else ""

        filename = f"{device_id}_{time.time()}_screen.png" if device_id else "screen.png"

        command = self.make_adb_command(path, f"{device_param}shell screencap -p /sdcard/{filename}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            return None, result.stderr

        # Pull the screenshot to local machine
        pull_cmd = self.make_adb_command(path, f"{device_param}pull /sdcard/{filename} {filename}")
        pull_result = subprocess.run(pull_cmd, shell=True, capture_output=True, text=True)

        if pull_result.returncode != 0:
            return None, pull_result.stderr

        return filename, None

    def tap(self, x: int, y: int) -> None:
        """
        Tap at the specified coordinates

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.run_command(f"shell input tap {x} {y}")

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> None:
        """
        Swipe from one point to another

        Args:
            x1: Starting X coordinate
            y1: Starting Y coordinate
            x2: Ending X coordinate
            y2: Ending Y coordinate
            duration: Swipe duration in milliseconds
        """
        self.run_command(f"shell input swipe {x1} {y1} {x2} {y2} {duration}")

    def input_text(self, text: str) -> None:
        """
        Input text on the device

        Args:
            text: Text to input
        """
        # Escape special characters for shell
        text = text.replace("'", "\\'").replace(" ", "%s")
        self.run_command(f"shell input text '{text}'")

    def press_key(self, keycode: str) -> None:
        """
        Press a key on the device

        Args:
            keycode: Key code (e.g., 'KEYCODE_HOME', 'KEYCODE_BACK')
            :param keycode:
            :param self:
        """
        if not keycode.startswith("KEYCODE_"):
            keycode = f"KEYCODE_{keycode}"

        self.run_command(f"shell input keyevent {keycode}")

    def launch_app(self, package_name: str) -> None:
        """
        Launch an application by package name

        Args:
            package_name: Package name of the app to launch
        """
        # Get launcher activity for the package
        result, error = self.run_command(f"shell cmd package resolve-activity --brief {package_name}")

        if error or (result and ((result.returncode != 0 or result.stderr) or ("No activity found" in result.stdout))):

            # Try direct method if activity resolution fails
            self.run_command(f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
        else:
            # Extract and launch the main activity
            stdout = result.stdout.strip()
            activity = stdout.splitlines()[1].strip()
            self.run_command(f"shell am start -n {activity}")


    def get_installed_packages(self) -> List[str]:
        """
        Get a list of installed packages on the device

        Returns:
            List of package names
        """
        stdout, _ = self.run_command("shell pm list packages")
        packages = []

        for line in stdout.splitlines():
            if line.startswith("package:"):
                package = line[8:].strip()  # Remove 'package:' prefix
                packages.append(package)

        return packages
