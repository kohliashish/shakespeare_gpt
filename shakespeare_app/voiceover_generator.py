from openai import OpenAI
from pathlib import Path
from flask import current_app as app

def generate_voiceover(text,voice="alloy"):
    api_key = app.config['OPENAI_API_KEY']
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=api_key,
    )

    response = client.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=text
    )
    speech_file_path = Path(__file__).parent / "resources/speech.mp3"
    response.stream_to_file(speech_file_path)
    return speech_file_path