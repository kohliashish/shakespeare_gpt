from flask import jsonify, request, send_file, render_template, make_response, send_from_directory
import re
from shakespeare_app import app
from shakespeare_app.story_generator import generate_story, extract_characters
from shakespeare_app.voiceover_generator import generate_voiceover
from shakespeare_app.image_generator import generate_image,generate_images
from shakespeare_app.video_generator import generate_video
from pydub import AudioSegment
from itertools import accumulate
from pathlib import Path


#Global Context
api_key = app.config['OPENAI_API_KEY']
audio_length = 0
images_path = []
global audio_path
audio_path = ''

def get_audio_duration(audio_path):
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/resources/<path:filename>')
def serve_resources(filename):
    return send_from_directory('resources', filename)

@app.route('/generateStory', methods=['POST'])
def story():
    data = request.get_json()
    prompt = data.get('prompt')
    context = data.get('context')
    if prompt:
        story = generate_story(prompt, context)
        return jsonify({'story': story}), 200
    else:
        return jsonify({'error': 'No prompt provided'}), 400

@app.route('/generateCharacters', methods=['POST'])
def characters():
    data = request.get_json()
    story = data.get('story')
    if story:
        characters = extract_characters(story)
        return jsonify({'characters': characters}), 200
    else:
        return jsonify({'error': 'No prompt provided'}), 400

@app.route('/generateFrames', methods=['POST'])
def frames():
    data = request.get_json()
    story = data.get('text')
    lines = []
    if story:
        lines = re.split(r'\.\s*', story)
        # Removing empty lines from the prompt list
        lines = [line for line in lines if line]
        # Creating a cumulative list of lines for retaining context
        lines_cumulative = list(accumulate(lines, lambda x, y: '. '.join([x, y])))
        images_path = generate_images(lines,lines_cumulative,len(lines),api_key)
        images_relative_paths = [str(Path('resources').joinpath(Path(p).name)) for p in images_path]
        return jsonify({'image_paths': images_relative_paths}), 200
    else:
        return jsonify({'error': 'No prompt provided'}), 400

@app.route('/generateVoiceOver',methods=['POST'])
def voiceover():
    try:
        data = request.get_json()
        story = data.get('text')
        voice = data.get('voice')
        if story and voice:
            voice_file = generate_voiceover(story, voice)
            response = make_response(send_file(voice_file, as_attachment=True, mimetype='audio/mpeg'))
            response.headers['Content-Type'] = 'audio/mpeg'
            return response
        elif story and not voice:
            voice_file = generate_voiceover(story)
            audio_length = get_audio_duration(voice_file)
            response = make_response(send_file(voice_file, as_attachment=True, mimetype='audio/mpeg'))
            response.headers['Content-Type'] = 'audio/mpeg'
            return response
        else:
            return jsonify({'error': 'No story provided'}), 400
    except Exception as e:
        return jsonify({'Endpoint error': str(e)}), 500

@app.route('/generateImage', methods=['POST'])
def images():
    data = request.get_json()
    prompt = data.get('character')
    character_name = data.get('name')
    if prompt:
        image_url = generate_image(prompt,character_name)
        # return jsonify({'image_url': image_url}), 200
        return send_file(image_url, as_attachment=True, mimetype='image/jpg')
    else:
        return jsonify({'error': 'No prompt provided'}), 400

@app.route('/generateVideo', methods=['POST'])
def video():
    data = request.get_json()
    imagefiles = data.get('imagefiles')
    images_path = [Path(app.root_path) / 'resources' / img_path.split('/')[-1] for img_path in imagefiles]
    audio_path = Path(app.root_path) / 'resources/speech.mp3'

    if images_path and audio_path:
        # image_paths = [Path(app.root_path) / 'resources' / img for img in imagefiles]
        # audio_path = Path(app.root_path) / 'resources' / voicefile
        video_path = generate_video(images_path, audio_path)
        video_relative_path = video_path.relative_to(Path(app.root_path))

        return jsonify({'video_path': str(video_relative_path)})
    else:
        return jsonify({'error': 'Missing image or voice file paths'}), 400