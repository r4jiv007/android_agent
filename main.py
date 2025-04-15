import os

from google import genai
from dotenv import load_dotenv
import pyadb
from pyadb import PyAdb

load_dotenv()

def main():
    pyadb = PyAdb()
    print(pyadb.list_android_devices())
    pyadb.launch_app("com.android.chrome")
    #take_screenshot()


if __name__ == "__main__":
    main()
