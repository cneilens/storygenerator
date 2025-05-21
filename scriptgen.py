import base64
import json
from openai import OpenAI
import os
from PIL import Image

client = OpenAI()

story = json.load(open("fbi-story.json", "r"))

# base_prompt = "Can you flesh this out into a script, also generate a story board and a set of prompts for generating images for the story board. Respond as a json response with the following keys: \n\n 1. script: The full script for the comic book, including dialogue and narration.\n 2. storyboard: A detailed description of each panel in the comic book, including character actions and settings.\n 3. image_prompts: A list of prompts for generating images for each panel in the comic book.\n\n The story is as follows:\n\n"
# prompt = "Its the night before the SuperBowl, an fat, old and lonely software engineer is sat in a bar eating dinner watching football clips. His phone rings, its an On Call Incident, he has to pay and rush out of the bar before finishing his dinner or sadly his beer. He runs home only to find the FBI are struggling to use the software he makes. If he doesn't solve the problem the Superbowl could be cancelled! He panics, raises the alarm and pulls in the real heroes to fix the problem."
# base_image_prompt = "Generate a photo realistic image given the following description. Use the first image for the person in the story, if there is no person in the first image, use the second image. Keep their main facial features so they remain recognizable as them. This is the description to use:\n\n"
# baseImage = "inbar.jpg"

base_prompt = story.get("baseprompt")
prompt = story.get("prompt")
base_image_prompt = story.get("base_image_prompt")
baseImage = story.get("baseImage")


response = client.responses.create(
    model="gpt-4.1",
    input=base_prompt + prompt,
    temperature=0.7,
)



print(response.output_text)
jsonresponse = response.output_text.removeprefix("```json\n")
jsonresponse = jsonresponse.removesuffix("\n```")

response = json.loads(jsonresponse)
# json.dump(response, open("script.json", "w"), indent=4)

prevImage = baseImage
for index, prompt in enumerate(response.get("image_prompts")):
    print (f"Generating image with prompt: {prompt}")
    result = client.images.edit(
        model="gpt-image-1",
        image=[open(prevImage, "rb"),
        open(baseImage, "rb")],
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