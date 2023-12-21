from openai import OpenAI
from flask import current_app as app
import json, re

def generate_story(prompt, max_tokens=4000):
    api_key = app.config['OPENAI_API_KEY']
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=api_key,
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "You are an intelligent story-writer. You create a short story in 150 words or less from the user content, that contains character development, an interesting plot and  climax. You ensure that the generated story does not use any generic phrases and provide detailed description of scenes."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.7
    )

    story = response.choices[0].message.content
    return story

def parse_characters(character_string):
    # Split the string by Markdown code block markers
    character_json_strings = character_string.split('```\n\n')

    parsed_characters = []
    for json_str in character_json_strings:
        # Remove Markdown code block markers and extra whitespace/newlines
        clean_json_str = re.sub(r'```json\n|\n```', '', json_str).strip()
        try:
            character = json.loads(clean_json_str)
            parsed_characters.append(character)
        except json.JSONDecodeError as e:
            print(f'Error parsing JSON: {e}')
            # Optionally handle the error, e.g., by continuing or returning an error response
    return parsed_characters

def generate_plain_text_description(characters):
    parsed_characters = parse_characters(characters)
    flattened_character_list = []
    for character in parsed_characters[0]:
        flattened = [k+" "+v+", " for k,v in character.items() if k != 'Name'] # Skip name and create plain text description of the character
        character["PlainText"] = ''.join(flattened)
        flattened_character_list.append(character)
    return flattened_character_list

def extract_characters(story_text, max_tokens=3000):
    api_key = app.config['OPENAI_API_KEY']
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=api_key,
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "You create a list of JSON objects of all the characters used in the story provided in the prompt. Each JSON object has 6 elements - 1. Name, 2. Gender, 3. Looks, 4. Nature and Personality, 5. Attire and, 6. Facial expression for each character."},
            {"role": "user", "content": story_text}
        ],
        max_tokens=max_tokens,
        temperature=0.5
    )

    characters = response.choices[0].message.content
    return generate_plain_text_description(characters)
