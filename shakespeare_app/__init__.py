from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Use environment variables via os.environ
app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

import shakespeare_app.views
