from openai import OpenAI
from openai import BadRequestError
from flask import current_app as app
from requests import get, post
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

chat_model_version = "gpt-4"
image_model_version = "dall-e-3"

def review_prompt(prompt,api_key):
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=api_key,
    )
    response = client.chat.completions.create(
        model=chat_model_version,
        messages=[
            {"role": "system", "content": "Please review the following prompt for potential content policy violations and re-write if needed."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    modified_prompt = response.choices[0].message.content
    return modified_prompt

    #Ask GPT to review and suggest modifications if necessary

def generate_image(prompt,context, name,batch_number,api_key):
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=api_key,
    )
    print(f"[INFO] Generating image for following prompt:\n\n{prompt}\n\n using the following context:\n\n{context}")
    # 
    initial_prompt=f"The image should be generated in tall mode. You look at the Context and then use the Prompt to generate the image. Create a hyperrealistic life-like image using the following Context: \n\n{context} and of the following prompt: \n\n{prompt}"
    # Re-write if the text contains any sensitive words that can potentially cause policy violations
    custom_prompt = review_prompt(initial_prompt, api_key)
    try:
        response = client.images.generate(
            model=image_model_version,
            prompt=custom_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url  # Assuming the response includes an image URL
        image_content = get(image_url) # Downloading the generated image from provided URL
        image_file_path = Path(__file__).parent / f"resources/inprocess/batch_{batch_number}_{name}.png"

        with open(image_file_path, 'wb') as f:
            f.write(image_content.content)

        return image_file_path
    except BadRequestError as e:
        print(f"OpenAI API Error: {e}")
        return "Error"

def generate_images(prompts, context, total_prompts, api_key):
    generated_images = []
    max_parallel_requests = 5
    print(f"[INFO] Generating {total_prompts} images")
    for i in range(0, total_prompts, max_parallel_requests):
        print("[INFO] Processing batch: ",i)
        prompt_batch = prompts[i:i + max_parallel_requests]
        context_batch = context[i:i + max_parallel_requests]
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_image = {executor.submit(generate_image, prompt[1], context_batch[prompt[0]], prompt[0], int(i/5), api_key): prompt for prompt in enumerate(prompt_batch)}
            for future in as_completed(future_to_image):
                image_path = future.result()
                generated_images.append(image_path)
        
        # Wait for 60 seconds after processing each batch, except for the last batch
        if i + max_parallel_requests < total_prompts:
            print("[INFO] Waiting 60 seconds before processing next batch")
            time.sleep(60)
    
    return generated_images