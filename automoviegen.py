import glob
from moviepy import AudioFileClip, CompositeAudioClip, ImageClip, concatenate_videoclips, CompositeVideoClip, vfx
import os
from PIL import Image, ImageFilter
from analyze_music_slideshow import analyze_music_transitions
from transitions import *

def resize_images(image_paths):

    resized_images = []
    max_height = 0

    # Step 1: Resize all to max height, keeping aspect ratio
    for path in image_paths:
        with Image.open(path) as img:
            img = img.convert("RGB")
            width, height = img.size
            if not path.endswith("-0.png"):
                max_height = max(max_height, height)
            resized_images.append((path, width, height, img))

    # Determine final resized dimensions
    resized_versions = []
    max_width = 0

    for path, orig_w, orig_h, img in resized_images:
        new_width = int((max_height / orig_h) * orig_w)
        max_width = max(max_width, new_width)
        if max_height == orig_h:
            resized_versions.append((path, img))
            continue
        print (f"Resizing {path} from {orig_w}x{orig_h} to max height {max_height}")
        resized = img.resize((new_width, max_height), Image.LANCZOS)
        resized_versions.append((path, resized))

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
                    music_enabled = True, music_file=None, crossfade_time=1):
    """
    Creates a slideshow video from images with crossfades between them.

    Args:
        image_folder: Folder containing the images
        output_file: Name of the output MP4 file
        image_pattern: Pattern to match image files (comma-separated patterns)
        music_enabled: Whether to add background music
        music_file: music file to add to the video
        crossfade_time: Duration of crossfade between images (in seconds)
    """

    if music_enabled and music_file is None:
        print("No music file provided!")
        return

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
    print(f"Music Enabled: {music_enabled}, Music file: {music_file}")
    if music_enabled:
        slides = analyze_music_transitions(music_file, len(image_files), crossfade_time, 3.0)
        slides_duration = slides.get("total_duration", 0)
        transitions = slides.get("slides")

    else:
        # If no music, use default transitions
        transitions = [{"duration": 2, "transition": crossfade_time} for _ in range(len(image_files) - 1)]
        transitions.append({"duration": 2, "transition": 3.0})  # Last slide has no transition
        slides_duration = sum([slide["duration"] + slide["transition"] for slide in transitions])


    # Create a clip for each image
    clips = []
    for index, img in enumerate(image_files):
        slide = transitions[index]
        if index == len(image_files) - 1:
            clip = ImageClip(img).with_duration(slide["duration"] + slide["transition"])
        else:
            clip = ImageClip(img).with_duration(slide["duration"])
        clips.append(clip)

    clips_with_transitions = []
    for i in range(0, len(clips) - 1):
        # Add crossfade transition
        clip1 = clips[i]
        clip2 = clips[i + 1]
        slide = transitions[i]
        transition_clip = ripple_transition(clip1, clip2, slide["transition"])
        clips_with_transitions.append(clip1)
        clips_with_transitions.append(transition_clip)
        i += 1
    clip = clips[-1]
    slide = transitions[-1]
    clips_with_transitions.append(clip.with_effects([vfx.FadeOut(slide["transition"])]))

    clips_duration = sum([clip.duration for clip in clips_with_transitions])

    print(f"Duration slides {slides_duration} clips {clips_duration}")
    # total = 0
    # for clip in clips_with_transitions:
    #     total += clip.duration
    #     print (f"Clip duration: {clip.duration} running total: {total}")

    # total = 0
    # for slide in transitions:
    #     total += slide["duration"]
    #     total += slide["transition"]
    #     combined = slide["duration"] + slide["transition"]
    #     print (f"Slide duration: {slide['duration']} transition: {slide['transition']} combined: {combined} running total: {total}")

    # Create the final video with crossfades
    final_clip = concatenate_videoclips(clips_with_transitions, method="chain", padding=0)

    if music_enabled and music_file:
        audioclip = AudioFileClip(music_file)
        print(f"Audio duration: {audioclip.duration}, Video duration: {final_clip.duration}")
        new_audioclip = CompositeAudioClip([audioclip]).with_duration(final_clip.duration)
        final_clip = final_clip.with_audio(new_audioclip)

    # Write the result to a file
    final_clip.write_videofile(output_file, fps=24, audio_codec='aac')
    print(f"Slideshow created successfully: {output_file}")

if __name__ == "__main__":
    # You can customize these parameters as needed
    # {image_folder}/vodevil-15550.mp3
    create_slideshow(
        image_folder="./",
        output_file="./letsrock-2.mp4",
        image_pattern="test-*.jpg,test-*.png",
        # music_file = "./music/cherry-stone-rock-205899.mp3",
        music_file = "./music/A1-Thunderstruck_01.mp3",
        crossfade_time=1.5
    )