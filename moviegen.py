import glob
from moviepy import AudioFileClip, CompositeAudioClip, ImageClip, concatenate_videoclips, CompositeVideoClip, vfx
import os
from PIL import Image, ImageFilter


def resize_images(image_paths):

    resized_images = []
    max_height = 0

    # Step 1: Resize all to max height, keeping aspect ratio
    for path in image_paths:
        with Image.open(path) as img:
            img = img.convert("RGB")
            width, height = img.size
            max_height = max(max_height, height)
            resized_images.append((path, width, height, img))

    # Determine final resized dimensions
    resized_versions = []
    max_width = 0

    for path, orig_w, orig_h, img in resized_images:
        if max_height == orig_h:
            resized_versions.append((path, img))
            continue
        print (f"Resizing {path} from {orig_w}x{orig_h} to max height {max_height}")
        new_width = int((max_height / orig_h) * orig_w)
        resized = img.resize((new_width, max_height), Image.LANCZOS)
        resized_versions.append((path, resized))
        max_width = max(max_width, new_width)

    # Step 2: Add blurred borders to portrait images if needed
    for path, resized in resized_versions:
        width, height = resized.size
        if width < max_width:
            # Create blurred background
            print (f"Adding blurred background to {path}")
            blurred = resized.copy().resize((max_width, max_height), Image.LANCZOS)
            blurred = blurred.filter(ImageFilter.GaussianBlur(radius=40))
            # Paste resized image in center
            offset_x = (max_width - width) // 2
            blurred.paste(resized, (offset_x, 0))
            final_img = blurred
        else:
            final_img = resized
        # Save result
        final_img.save(path)

def create_slideshow(image_folder=".", output_file="slideshow.mp4", image_pattern="test-*.jpg,test-*.png", 
                    display_time=4, crossfade_time=1):
    """
    Creates a slideshow video from images with crossfades between them.
    
    Args:
        image_folder: Folder containing the images
        output_file: Name of the output MP4 file
        image_pattern: Pattern to match image files (comma-separated patterns)
        display_time: Time each image is displayed (in seconds)
        crossfade_time: Duration of crossfade between images (in seconds)
    """
    # Get list of all image files matching the pattern
    patterns = image_pattern.split(",")
    image_files = []
    for pattern in patterns:
        image_files.extend(glob.glob(os.path.join(image_folder, pattern)))
    
    if not image_files:
        print("No images found matching the pattern!")
        return
    
    # Sort the images based on their index in the filename
    def extract_index(filename):
        base = os.path.basename(filename)
        try:
            # Extract number between "test-" and file extension
            index_str = base.split("test-")[1].split(".")[0]
            return int(index_str)
        except (IndexError, ValueError):
            return float('inf')  # Files without proper index go to the end
    
    image_files.sort(key=extract_index)
    
    resize_images(image_files)
    
    # Create a clip for each image
    clips = []
    for img in image_files:
        clip = ImageClip(img).with_duration(display_time).with_effects([vfx.CrossFadeIn(1.5),vfx.CrossFadeOut(1.5)])
        clips.append(clip)
    
    audioclip = AudioFileClip(f"{image_folder}/vodevil-15550.mp3")
    new_audioclip = CompositeAudioClip([audioclip])
    
    # Create the final video with crossfades
    final_clip = concatenate_videoclips(clips, method="compose", padding=-crossfade_time)
    final_clip.audio = new_audioclip
    # Write the result to a file
    final_clip.write_videofile(output_file, fps=24)
    print(f"Slideshow created successfully: {output_file}")

if __name__ == "__main__":
    # You can customize these parameters as needed
    create_slideshow(
        image_folder="./clownstory",  # Current directory
        output_file="./clownstory/slideshow.mp4",
        image_pattern="test-*.jpg,test-*.png",
        display_time=4,  # Each image displays for 4 seconds
        crossfade_time=1  # 1 second crossfade
    )