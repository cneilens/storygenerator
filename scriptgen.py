import base64
import json
from openai import OpenAI
import os
from PIL import Image
from automoviegen import create_slideshow
import glob

client = OpenAI()

story_file = "rockstar_story.json"
response_file, ext = os.path.splitext(story_file)
response_file = response_file + "_response" + ext

story = json.load(open(story_file, "r"))

base_prompt = story.get("baseprompt")
prompt = story.get("prompt")
base_image_prompt = story.get("base_image_prompt")
baseImage = story.get("baseImage")
music = story.get("music")

response = client.responses.create(
    model="gpt-4.1",
    input=base_prompt + prompt,
    temperature=0.7,
)

print(response.output_text)
jsonresponse = response.output_text.removeprefix("```json\n")
jsonresponse = jsonresponse.removesuffix("\n```")

response = json.loads(jsonresponse)
json.dump(response, open(response_file, "w"), indent=4)

for img_path in glob.glob("test-*.png"):
    try:
        os.remove(img_path)
        print(f"Deleted {img_path}")
    except OSError as e:
        print(f"Error deleting {img_path}: {e}")

numImages = 0
prevImage = baseImage
for index, prompt in enumerate(response.get("image_prompts")):
    print (f"Generating image with prompt: {prompt}")
    result = client.images.edit(
        model="gpt-image-1",
        image=[
            open(baseImage, "rb"),
            open(prevImage, "rb")
        ],
        prompt=base_image_prompt + prompt
    )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    imageFileName = f"test-{index+1}.png"
    print(f"Image {imageFileName} generated successfully.")
    # Save the image to a file
    with open(imageFileName, "wb") as f:
        f.write(image_bytes)
    prevImage = imageFileName
    numImages += 1

with open(baseImage, "rb") as f1:
    image_bytes = f1.read()
    # Save the image to a file
    with open("test-0.png", "wb") as f:
        f.write(image_bytes)
numImages += 1

mp4_file, ext = os.path.splitext(story_file)
mp4_file = mp4_file + ".mp4"

create_slideshow(
        image_folder = "./", 
        output_file = mp4_file,
        image_pattern = "test-*.png",
        music_file = music,
        crossfade_time = 1.5 
    )