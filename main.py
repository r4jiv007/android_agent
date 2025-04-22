import os
import time

from google import genai
from google.genai import  types
from dotenv import load_dotenv
import pyadb
from pyadb import PyAdb, function_declarations
from PIL import Image

load_dotenv()

# Generation Config with Function Declaration

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
tools = types.Tool(function_declarations=function_declarations)
config = types.GenerateContentConfig(tools=[tools],
                                     system_instruction=
"""
Role & Persona:
You are 'QA-Droid', an AI assistant specialized in controlling Android devices (physical, emulators, network-connected) via the functions provided to you via the SDK. Your persona is that of a meticulous, observant, and precise Manual QA Tester. You interact with the device exclusively through a set of provided ADB tools.

Core Objective:
Execute test steps or commands provided in natural language.
Translate these instructions into sequences of actions using functions provided to you via the SDK.
Interact with any application or system screen on the connected device as directed, aiming to replicate human tester actions.
Report outcomes, observations, or errors based on tool results and screenshot analysis.

Operational Strategy & Workflow (CRITICAL):
functions provided: All device interactions MUST use the provided function tools (details supplied via the SDK).
Screenshot Reliance: You DO NOT have direct access to the UI object hierarchy. Your understanding of the screen state depends entirely on analyzing screenshots.
Mandatory Workflow for Visual UI Interaction: When asked to interact with a specific UI element (e.g., "tap button X", "enter text in field Y"):

If requried you will be provided with screenshot of current visual state.

Analyze this screenshot using your multimodal capabilities to locate the target element and determine necessary parameters (e.g., coordinates for tap/swipe , identify input fields).

Execute the action using the most specific interaction tool available.
Tool Prioritization: Utilize the specialized tools provided (for tapping, swiping, text input, key presses, app launching, getting device info, etc.) whenever applicable. Use the generic run_command tool only for ADB actions not covered by specific tools, and do so cautiously.
Device Context: Use tools for listing devices and getting device details as needed, especially if multiple devices might be connected. Ensure you target the correct device ID if required by the tools.

Interaction Rules & Guidelines:
Precision: Execute commands accurately based on your interpretation of the instructions and screenshot analysis.
Completeness: Return success in json format "{success: true}" .Ensure you have completed the task before reporting success.
Ambiguity Resolution: If a command is unclear or multiple visual elements match a description in the screenshot, state the ambiguity and ask the user for clarification before acting. ("Based on the screenshot, I see [Option A] and [Option B]. Which should I interact with?")
Error Reporting: Clearly report any failures encountered while using the tools (e.g., ADB errors, inability to find an element in the screenshot). Do not guess or proceed if uncertain.
Information Requests: Use the appropriate tools to answer user questions about device status, installed packages, etc.
Tool Awareness: Refer to the descriptions of the provided tools (available via the SDK) if you need clarification on their specific function or required parameters.

Your primary directive is to function as a reliable QA agent, navigating and interacting with the Android device via ADB commands derived from user instructions and visual screenshot analysis, using the provided tools effectively and safely.

""")


def main():
    pyadb = PyAdb()
    # pyadb.take_screenshot()
    # return
    function_map = {
        "check_if_adb_installed": pyadb.check_if_adb_installed,
        "make_adb_command": pyadb.make_adb_command,
        "run_command": pyadb.run_command,
        "get_device_details": pyadb.get_device_details,
        "list_android_devices": pyadb.list_android_devices,
        "launch_app": pyadb.launch_app,
        "take_screenshot": pyadb.take_screenshot,
        "tap": pyadb.tap,
        "swipe": pyadb.swipe,
        "input_text": pyadb.input_text,
        "press_key": pyadb.press_key,
        "get_installed_packages": pyadb.get_installed_packages
    }
   
    contents = [
        types.Content(
            role="user", parts=[types.Part(text="launch the chrome app in my connected device and open gmail on it")]
        ) 
    ]

    while True:
        # Send request with function declarations
        response = client.models.generate_content(
            model="gemini-2.0-flash", config=config, contents=contents
        )
        if (response.candidates[0].content.parts[0].text and "success" in response.candidates[0].content.parts[0].text) or (response.text and "success" in response.text):
            break
        
        if response.text:
            print(response.text)
        if response.function_calls:
            print(response.function_calls)

            for function_call in response.function_calls:
                tool_call = function_call
  
            
                # Append the model's function call message
            
                # Execute the function if it exists in the map
                if tool_call.name in function_map:
                    contents.append(types.Content(role="model", parts=[types.Part(function_call=tool_call)]))

                    result = function_map[tool_call.name](**tool_call.args)
                    time.sleep(1)
                    print(f"Function execution result: {result}")
                    screen,error_screen = pyadb.take_screenshot()
                    if(error_screen):
                        print(f"Error taking screenshot: {error_screen}")
                        function_response_part_screenshot_error = types.Part.text(f"Error taking screenshot: {error_screen}")
                        parts=[function_response_part_screenshot_error]
                    else:
                        parts=[types.Part.from_bytes(data=screen, mime_type="image/png")]

                    if result: 
                        if isinstance(result, bytes):
                            function_response_part = types.Part.from_function_response(
                                name=tool_call.name,
                                response={"result": "attaching screenshot"},
                            )
                            parts.append(function_response_part)
                        else:
                            function_response_part = types.Part.from_function_response(
                                name=tool_call.name,
                                response={"result": result},
                            )
                            parts.append(function_response_part)

                        
                    else:
                        function_response_part = types.Part.from_function_response(
                            name=tool_call.name,
                            response={"result": "unknown state"},
                        )
                        parts=[function_response_part]
                        
                    contents.append(types.Content(role="user", parts=parts))
                else:
                    parts.append(types.Part.text(text=f"Unknown function: {tool_call.name}"))
                    print(f"Unknown function: {tool_call.name}")
                    contents.append(types.Content(role="user", parts=parts))


            



    # print(pyadb.list_android_devices())
    # pyadb.launch_app("com.android.chrome")
    #take_screenshot()


if __name__ == "__main__":
    main()
