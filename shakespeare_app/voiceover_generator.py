from openai import OpenAI
from pathlib import Path
from flask import current_app as app

def generate_voiceover(text,api_key,model_version,voice="alloy"):
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=api_key,
    )

    response = client.audio.speech.create(
        model=model_version,
        voice=voice,
        input=text
    )
    speech_file_path = Path(__file__).parent / "resources/inprocess/speech.mp3"
    response.stream_to_file(speech_file_path)
    return speech_file_path