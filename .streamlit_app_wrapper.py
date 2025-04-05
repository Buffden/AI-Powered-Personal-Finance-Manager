import os
import sys

# Ensure the root of the project is in the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import and run the app
import frontend.streamlit_app
