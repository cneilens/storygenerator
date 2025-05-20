import base64
import json
from openai import OpenAI
import os
from PIL import Image

client = OpenAI()


jsonStory = json.load(open("superhero-story.json", "r"))
baseprompt = jsonStory.get("story").get("baseprompt")
prompts = jsonStory.get("story").get("prompts")
baseImage = jsonStory.get("story").get("baseimage")
prevImage = baseImage

with Image.open(baseImage) as img:
    base, ext = os.path.splitext(baseImage)
    img.save(f"test-0.{ext}")  
    
for index, prompt in enumerate(prompts):
    result = None
    print (f"Generating image {index} with prompt: {prompt}")
    if index == 0:
        result = client.images.edit(
            model="gpt-image-1",
            image=open(prevImage, "rb"),
            prompt=baseprompt + prompt
        )
    else:
        result = client.images.edit(
            model="gpt-image-1",
            image=[
                open("inbar.jpg", "rb"),
                open(prevImage, "rb")
            ],
            prompt=baseprompt + prompt,
        )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    imageFileName = f"test-{index+1}.png"
    print(f"Image {imageFileName} generated successfully.")
    # Save the image to a file
    with open(imageFileName, "wb") as f:
        f.write(image_bytes)
    prevImage = imageFileName
