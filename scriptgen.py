import argparse
import base64
import json
from openai import OpenAI
import os
from PIL import Image
from automoviegen import create_slideshow
from scriptomusic import get_best_track_for_script
import glob
import sys

client = OpenAI()

story_file = "rockstar_story.json"

def fix_prompt(prompt):
    response = client.responses.create(
        model="gpt-4.1-mini",
        input="Please make a variation of the following prompt that would be less offensive and pass openAIs safety rules. \nIf the prompt says the person was overweight reword it into less offensive terms while keeping the meaning. \nReturn only the new prompt as a string. \n\nPrompt:" + prompt,
        temperature=0.7,
    )
    return response.output_text.strip()
    

def send_prompt(prompt, prevImage, baseImage, base_image_prompt, feedback_image, iteration=0):
    try:
        if feedback_image and prevImage:
            result = client.images.edit(
                model="gpt-image-1",
                image=[
                    open(baseImage, "rb"),
                    open(prevImage, "rb")
                ],
                quality="low",
                size="1536x1024",
                prompt=base_image_prompt + prompt
            )
        else:
            result = client.images.edit(
                model="gpt-image-1",
                image=open(baseImage, "rb"),
                quality="low",
                size="1536x1024",
                prompt=base_image_prompt + prompt
            )
    except Exception as e:
        print(f"Error generating image: {e}")
        if iteration < 3:
            fixed_prompt = fix_prompt(prompt)
            print(f"Retrying with a fixed prompt {fixed_prompt} ...")
            return send_prompt(fixed_prompt, prevImage, baseImage, base_image_prompt, feedback_image, iteration + 1)
        else:
            print("Failed to generate image after multiple attempts.")
        return None
    return result
       
def process_responsefile(response_file,
                         story_file, 
                         min_length=70,
                         max_length=120,
                         crossfade_time=1.5,
                         musichints="",
                         skip_image_gen=False, 
                         feedback_image=False):
    
    print(f"Story file: {story_file}")
    story = json.load(open(story_file, "r"))

    base_prompt = story.get("baseprompt")
    prompt = story.get("prompt")
    base_image_prompt = story.get("base_image_prompt")
    baseImage = story.get("baseImage")
    music = story.get("music")

    print(f"Base image: {baseImage}")
    print(f"Music: {music}")
    print(f"Base prompt: {base_prompt}")
    print(f"Prompt: {prompt}")
    print(f"Base image prompt: {base_image_prompt}")
    
    response = json.load(open(response_file, "r"))
    script_folder = os.path.dirname(story_file)
    mp4_file, _ = os.path.splitext(story_file)
    mp4_file = os.path.join(script_folder,  mp4_file + ".mp4")
    
    with Image.open(baseImage) as img:
        img = img.convert("RGB")
        width, height = img.size
        baseImageDownSized = os.path.join(script_folder, "baseimage_downsized.png")
        img.resize((int(width/2), int(height/2)), Image.LANCZOS).save(baseImageDownSized)

    if not skip_image_gen:
        print("Generating images...")
        for img_path in glob.glob("test-*.png", root_dir=script_folder):
            try:
                os.remove(os.path.join(script_folder, img_path))
                print(f"Deleted {img_path}")
            except OSError as e:
                print(f"Error deleting {img_path}: {e}")
        prevImage = None
        for index, prompt in enumerate(response.get("image_prompts")):
            print (f"Generating image with prompt: {prompt}")
            result = send_prompt(prompt, prevImage, baseImageDownSized, base_image_prompt, feedback_image)
            if not result:
                continue
            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)
            imageFileName = f"test-{index+1}.png"
            imageFileName = os.path.join(script_folder, imageFileName)
            print(f"Image {imageFileName} generated successfully.")
            # Save the image to a file
            with open(imageFileName, "wb") as f:
                f.write(image_bytes)
                
            with Image.open(imageFileName) as img:
                img = img.convert("RGB")
                width, height = img.size
                prevImage = os.path.join(script_folder, "previmage.png")
                img.resize((int(width/2), int(height/2)), Image.LANCZOS).save(prevImage)

        with open(baseImage, "rb") as f1:
            image_bytes = f1.read()
            # Save the image to a file
            with open(os.path.join(script_folder, "test-0.png"), "wb") as f:
                f.write(image_bytes)

    numslides = 0
    for img_path in glob.glob("test-*.png", root_dir=script_folder):
        numslides += 1

    best_music = get_best_track_for_script(response.get("script"), numslides=numslides, min_length=min_length, max_length=max_length, hints=musichints, refreshCache=False)
    if not best_music:
        best_music = music
    
    print(f"Using music: {best_music}")
    print(f"Script folder: {script_folder}")
    print(f"Output MP4 file: {mp4_file}")
    create_slideshow(
            image_folder = script_folder, 
            output_file = mp4_file,
            image_pattern = "test-*.png",
            music_file = best_music,
            crossfade_time = crossfade_time
        )    
        
            
def script_gen(story_file, 
               min_length=70,
               max_length=120,
               crossfade_time=1.5,
               musichints="",
               skip_image_gen=False, 
               feedback_image=False):
    response_file, ext = os.path.splitext(story_file)
    response_file = response_file + "_response" + ext
    script_folder = os.path.dirname(story_file)

    print(f"Story file: {story_file}")
    story = json.load(open(story_file, "r"))

    base_prompt = story.get("baseprompt")
    prompt = story.get("prompt")
    base_image_prompt = story.get("base_image_prompt")
    baseImage = story.get("baseImage")
    music = story.get("music")
    print(f"Base image: {baseImage}")
    print(f"Music: {music}")
    print(f"Base prompt: {base_prompt}")
    print(f"Prompt: {prompt}")
    print(f"Base image prompt: {base_image_prompt}")
    
    print("Generating script...")
    response = client.responses.create(
        model="gpt-4.1",
        input=base_prompt + prompt,
        temperature=0.7,
    )

    print(response.output_text)
    jsonresponse = response.output_text.removeprefix("```json")
    jsonresponse = jsonresponse.removesuffix("```")
    jsonresponse = jsonresponse.replace("\'", "'")
    response = json.loads(jsonresponse)
    json.dump(response, open(response_file, "w"), indent=4)

    process_responsefile(
        response_file, 
        story_file=story_file,
        min_length=min_length,
        max_length=max_length,
        crossfade_time=crossfade_time,
        musichints=musichints,
        skip_image_gen=skip_image_gen,
        feedback_image=feedback_image
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a script from a story file')
    parser.add_argument('story_file', type=str, help='Path to the story JSON file')
    parser.add_argument('min_length', type=float, help='Minimum length of the video in seconds', default=70) 
    parser.add_argument('max_length', type=float, help='Maximum length of the video in seconds', default=120)
    parser.add_argument('crossfade_time', type=float, help='Crossfade time in seconds', default=1.5)
    parser.add_argument('musichints', type=str, help='Music hints for the script generation', default="")
    parser.add_argument('--response_file', type=str, help='Path to the response JSON file', default=None, required=False)
    parser.add_argument('--skip_image_gen', action='store_true', help='Skip image generation step', default=False)
    parser.add_argument('--feedback_image', action='store_true', help='Feedback previous image', default=False)
    
    args = parser.parse_args()
    if args.response_file:
        response_file = args.response_file
        if not os.path.exists(response_file):
            print(f"Response file {response_file} does not exist. exiting.")
            exit(1)
        process_responsefile(
            response_file, 
            story_file=args.story_file,
            min_length=args.min_length,
            max_length=args.max_length,
            crossfade_time=args.crossfade_time,
            musichints=args.musichints,
            skip_image_gen=args.skip_image_gen,
            feedback_image=args.feedback_image
        )
    else:    
        script_gen(args.story_file,
                args.min_length,
                args.max_length,
                args.crossfade_time,
                args.musichints,
                args.skip_image_gen, 
                args.feedback_image)
