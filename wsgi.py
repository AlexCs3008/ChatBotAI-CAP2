import os
import sys

# Get the absolute path of the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the current directory to Python path
sys.path.insert(0, current_dir)

# Import your Flask app
from backend.app import app as application

# Make the app available to Gunicorn
app = application