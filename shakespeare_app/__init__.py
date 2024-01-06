from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Use environment variables via os.environ
app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
app.config['OPENAI_TEXT_MODEL'] = os.getenv('OPENAI_TEXT_MODEL')
app.config['OPENAI_IMAGE_MODEL'] = os.getenv('OPENAI_IMAGE_MODEL')
app.config['OPENAI_TTS_MODEL'] = os.getenv('OPENAI_TTS_MODEL')

import shakespeare_app.views
