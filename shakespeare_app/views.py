from flask import jsonify, request, send_file, render_template, make_response, send_from_directory
import re, random
from shakespeare_app import app
from shakespeare_app.story_generator import generate_story, extract_characters, identify_metadata
from shakespeare_app.voiceover_generator import generate_voiceover
from shakespeare_app.image_generator import generate_image,generate_images
from shakespeare_app.video_generator import generate_video
from itertools import accumulate
from pathlib import Path
import git, json


#Global Context
api_key = app.config['OPENAI_API_KEY']
text_model_version = app.config['OPENAI_TEXT_MODEL']
image_model_version = app.config['OPENAI_IMAGE_MODEL']
tts_model_version = app.config['OPENAI_TTS_MODEL']
audio_length = 0
images_path = []
tts_voices = ["alloy","echo","fable","onyx","nova","shimmer"]
global audio_path
audio_path = ''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_server', methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('https://github.com/kohlisaab/shakespeare_gpt.git')
        origin = repo.remotes.origin
        origin.pull()
        return jsonify({'success': 'Updated PythonAnywhere successfully'}), 200
    else:
        return jsonify({'error': 'Wrong event type'}), 400

@app.route('/resources/<path:filename>')
def serve_resources(filename):
    return send_from_directory('resources', filename)

@app.route('/resources/inprocess/<path:filename>')
def serve_inprocess_files(filename):
    return send_from_directory('resources/inprocess', filename)

@app.route('/generateStory', methods=['POST'])
def story():
    data = request.get_json()
    prompt = data.get('prompt')
    context = data.get('context')
    if prompt:
        story = generate_story(prompt, context, api_key, text_model_version)
        return jsonify({'story': story}), 200
    else:
        return jsonify({'error': 'No prompt provided'}), 400

@app.route('/generateCharacters', methods=['POST'])
def characters():
    data = request.get_json()
    story = data.get('story')
    if story:
        characters = extract_characters(story, api_key, text_model_version)
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
        images_path = generate_images(lines,lines_cumulative,len(lines),api_key,image_model_version,text_model_version)
        images_relative_paths = [str(Path('resources/inprocess').joinpath(Path(p).name)) for p in images_path]
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
            voice_file = generate_voiceover(story, api_key, tts_model_version, voice)
            response = make_response(send_file(voice_file, as_attachment=True, mimetype='audio/mpeg'))
            response.headers['Content-Type'] = 'audio/mpeg'
            return response
        elif story and not voice:
            voice = random.choice(tts_voices)
            voice_file = generate_voiceover(story, api_key, tts_model_version, voice)
            response = make_response(send_file(voice_file, as_attachment=True, mimetype='audio/mpeg'))
            response.headers['Content-Type'] = 'audio/mpeg'
            return response
        else:
            return jsonify({'error': 'No story provided'}), 400
    except Exception as e:
        return jsonify({'Endpoint error': str(e)}), 500

@app.route('/generateImage', methods=['POST'])
def images():
    batch = random.randint(0,99)
    data = request.get_json()
    prompt = data.get('prompt')
    image_name = data.get('name')
    context = data.get('context')
    if prompt and image_name and context:
        image_url = generate_image(prompt, context, image_name, batch, api_key, image_model_version, text_model_version)
        return send_file(image_url, as_attachment=True, mimetype='image/jpg')
    elif prompt and not image_name:
        image_name = random.randint(0,99)
        if context:
            image_url = generate_image(prompt, context, image_name, batch, api_key, image_model_version, text_model_version)
            return send_file(image_url, as_attachment=True, mimetype='image/jpg')
        else:
            #Default context in it's absence
            context = 'The image should be life-like and ultra high definition.'
            image_url = generate_image(prompt, context, image_name, batch, api_key, image_model_version, text_model_version)
            return send_file(image_url, as_attachment=True, mimetype='image/jpg')
    else:
        return jsonify({'error': 'No prompt provided'}), 400

@app.route('/generateVideo', methods=['POST'])
def video():
    data = request.get_json()
    imagefiles = data.get('imagefiles')
    metadata = data.get('metadata')
    background_volume = data.get('background_volume')

    images_path = [Path(app.root_path) / 'resources/inprocess' / img_path.split('/')[-1] for img_path in imagefiles]
    audio_path = Path(app.root_path) / 'resources/inprocess/speech.mp3'

    if images_path and audio_path and metadata and background_volume:
        video_path = generate_video(images_path, audio_path, metadata, background_volume = background_volume)
        video_relative_path = video_path.relative_to(Path(app.root_path))
        return jsonify({'video_path': str(video_relative_path)})
    else:
        return jsonify({'error': 'Missing image or voice file paths or metadata'}), 400
    
@app.route('/generateMetadata', methods=['POST'])
def metadata():
    data = request.get_json()
    story = data.get('story')
    if story:
        metadata = identify_metadata(story, api_key, text_model_version)
        return jsonify({'metadata': metadata}), 200
    else:
        return jsonify({'error': 'No story provided'}), 400
