import base64
import glob
import json
from openai import OpenAI
import os
from PIL import Image


client = OpenAI()

jsonComic = json.load(open("superhero-comic.json", "r"))
basePrompt = "Convert the following text description into a comic book page. The comic should have 6 cells, with each cell focusing on the characters and their actions through main points of the story. The style should be colorful and dynamic, suitable for a superhero comic.\n\n "
baseImage = jsonComic.get("baseimage")
comicbook_images_filenames=[]
# for index, comic in enumerate(jsonComic.get("comics")):
#     comicName = comic.get("title")
#     comicSummary = comic.get("summary")
#     look = comic.get("look")
#     if comic.get("hints"):
#         look += " " + comic.get("hints")
#     prompt = basePrompt + f"The title for the comic is {comicName}. The text description is {comicSummary} + {look}."
    
#     result = None
#     print (f"Generating image {index} for: {comicSummary}")
#     result = client.images.generate(
#         model="gpt-image-1",
#         prompt=prompt
#     )
#     image_base64 = result.data[0].b64_json
#     image_bytes = base64.b64decode(image_base64)
#     imageFileName = f"{index+1:02d}-{comicName}.png"
#     print(f"Image {imageFileName} generated successfully.")
#     # Save the image to a file
#     with open(imageFileName, "wb") as f:
#         f.write(image_bytes)
#     comicbook_images_filenames.append(imageFileName)

# Save all images to a PDF (first image is base, rest are appended)
comicbook_images_filenames = sorted(glob.glob("[0-9][0-9]-*.png"))
comicbook_images = []
for image_path in comicbook_images_filenames:
    img = Image.open(image_path)
    comicbook_images.append(img)

comicFileName=f"CaptainYesterday.pdf"
comicbook_images[0].save(comicFileName, save_all=True, append_images=comicbook_images[1:])
print(f"PDF saved to {comicFileName}")

realistic_comicbook_image_filenames=[]
for index, comic_image_name in enumerate(comicbook_images_filenames):
    base, ext = os.path.splitext(comic_image_name)
    result = client.images.edit(
        model="gpt-image-1",
        image=[
            open(comic_image_name, "rb"),
            open(baseImage, "rb")
        ],
        prompt="Make a photo realistic version of every cell in the comic strip by taking the person from the second photo and making him the superhero in the comic strip in the first image.\nKeep the look of the person in the second photo so he is easily recognizable.\nIf the superheros face is visible, keep the persons main facial features so its a close the super heroe is easily recognizable as the person.\nKeep any text and titles in the comic the same. Keep the formatting and style fo the text.",
    )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    imageFileName = f"{base}-realistic.png"
    print(f"Image {imageFileName} generated successfully.")
    # Save the image to a file
    with open(imageFileName, "wb") as f:
        f.write(image_bytes)
    realistic_comicbook_image_filenames.append(imageFileName)

comicFileName=f"CaptainYesterday-realistic.pdf"
comicbook_images = []
for image_path in realistic_comicbook_image_filenames:
    img = Image.open(image_path)
    comicbook_images.append(img)

comicbook_images[0].save(comicFileName, save_all=True, append_images=comicbook_images[1:])
print(f"PDF saved to {comicFileName}")