import os

from google import genai
from google.genai import  types
from dotenv import load_dotenv
import pyadb
from pyadb import PyAdb, function_declarations

load_dotenv()

# Generation Config with Function Declaration

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
tools = types.Tool(function_declarations=function_declarations)
config = types.GenerateContentConfig(tools=[tools])

def main():
    contents = [
        types.Content(
            role="user", parts=[types.Part(text="launch com.android.chrome on my connected android device")]
        )
    ]

    # Send request with function declarations
    response = client.models.generate_content(
        model="gemini-2.0-flash", config=config, contents=contents
    )
    print(response.candidates[0].content.parts[0].function_call)

    tool_call = response.candidates[0].content.parts[0].function_call
    pyadb = PyAdb()
    if tool_call.name == "list_android_devices":
        result = pyadb.list_android_devices(**tool_call.args)
        print(f"Function execution result: {result}")
    if tool_call.name == "launch_app":
        result = pyadb.launch_app(**tool_call.args)
        print(f"Function execution result: {result}")

    # print(pyadb.list_android_devices())
    # pyadb.launch_app("com.android.chrome")
    #take_screenshot()


if __name__ == "__main__":
    main()
