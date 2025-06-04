#!/usr/bin/env python3
import glob
import json
import os
import subprocess
from pathlib import Path
from nicegui import app, ui
import asyncio
import shutil
from local_file_picker import local_file_picker
from scriptomusic import download_genres

class PromptEditor:
    def __init__(self):
        self.baseprompt = ""
        self.prompt = ""
        self.base_image_prompt = ""
        self.baseimage_path = ""
        self.rootFolder = Path.cwd()  # Set the root folder to current working directory
        self.feedback_enabled = False
        self.music_enabled = True
        # Load prompts.json on startup if it exists
        if Path("prompts.json").exists():
            try:
                with open("prompts.json", "r") as f:
                    data = json.load(f)
                self.baseprompt = data.get("baseprompt", "")
                self.prompt = data.get("prompt", "")
                self.base_image_prompt = data.get("base_image_prompt", "")
                self.baseimage_path = data.get("baseImage", "")
            except Exception as e:
                print(f"Error loading prompts.json on startup: {str(e)}")
        self.load_incompetech_genres()

    async def save_to_json(self):
        # Return a future that completes when dialog is closed
        loop = asyncio.get_running_loop()
        closed = loop.create_future()

        # Create a dialog for filename input
        with ui.dialog().classes('w-full') as save_dialog, ui.card().classes('w-full'):
            ui.label('Save Prompts').classes('text-lg font-bold mb-4')

            filename_input = ui.input(
                label = 'Filename',
                placeholder = 'Enter filename (without .json extension)',
                value = self.load_file_input.value if self.load_file_input.value else 'prompts'
            ).classes('w-full')

            with ui.row():
                ui.button('Cancel', on_click=save_dialog.close)

                async def do_save():
                    filename = filename_input.value.strip()
                    if not filename:
                        ui.notify("Please enter a filename", type="warning")
                        return
                    # Add .json extension if not present
                    if not filename.endswith('.json'):
                        filename += '.json'

                    filename = os.path.join(self.rootFolder, filename)
                    editor.load_file_input.set_value(filename)
                    data = {
                        "baseprompt": self.baseprompt,
                        "prompt": self.prompt,
                        "base_image_prompt": self.base_image_prompt,
                        "baseImage": self.baseimage_path,
                    }

                    try:
                        with open(filename, "w") as f:
                            json.dump(data, f, indent=2)

                        ui.notify(f"Data saved to {filename}", type="positive")
                        save_dialog.close()
                    except Exception as e:
                        ui.notify(f"Error saving file: {str(e)}", type="negative")
                    closed.set_result(True)

                ui.button('Save', on_click=do_save).props('color=primary')

        save_dialog.open()

        # Wait for dialog to close
        await closed

    def load_from_json(self):
        file_path = self.load_file_input.value
        if not file_path:
            ui.notify("Please select a JSON file", type="warning")
            return

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            self.baseprompt_textarea.value = data.get("baseprompt", "")
            self.prompt_textarea.value = data.get("prompt", "")
            self.base_image_prompt_textarea.value = data.get("base_image_prompt", "")
            self.baseimage_path = data.get("baseImage", "")
            self.rootFolder = Path(file_path).parent
            self.baseimage_label.text = f"Selected: {Path(self.baseimage_path).name}" if self.baseimage_path else "No image selected"

            ui.notify(f"Loaded from {file_path}", type="positive")
        except Exception as e:
            ui.notify(f"Error loading file: {str(e)}", type="negative")

    def load_incompetech_genres(self):
        """Load genres from incompetech_genre.json file"""
        try:
            download_genres(force=False)
            genre_file = Path("./incompetech_genre.json")
            if not genre_file.exists():
                ui.notify("incompetech_genre.json file not found", type="warning")
                return []

            with open(genre_file, "r") as f:
                data = json.load(f)

            # Extract all unique genres from the data
            genres = set()
            for item in data:
                if "genre" in item:
                    genre = item["genre"]
                    if isinstance(genre, list):
                        genres.update(genre)
                    else:
                        genres.add(genre)

            # Convert to sorted list
            self.genre_list = sorted(list(genres))

        except Exception as e:
            ui.notify(f"Error loading genres: {str(e)}", type="negative")

    async def run_script(self,
                         use_last_output,
                         run_image_gen):

        minlength = self.min_length_input.value
        maxlength = self.max_length_input.value
        transition = self.transition_input.value
        music_enabled = self.music_enabled_checkbox.value
        feedback_last_image = self.feedback_enabled
        music_hints = editor.hints_input.value if hasattr(editor, 'hints_input') else ""
        music_hints = music_hints + editor.selected_genre if hasattr(editor, 'selected_genre') and editor.selected_genre else music_hints

        await self.save_to_json()

        try:
            # Create dialog with log and image side-by-side
            if not hasattr(editor, 'log_dialog'):
                with ui.dialog().classes('w-full') as editor.log_dialog:
                    with ui.card().classes('w-full'):
                        ui.label('Script Output').classes('text-xl font-bold mb-4')
                        with ui.row().classes('w-full gap-4'):
                            # Log window on the left
                            with ui.column().classes('w-full'):
                                ui.label('Log Output').classes('text-lg font-semibold mb-2')
                                editor.log_output = ui.log(max_lines=1000).classes('w-full h-96')

                            # Image view on the right
                            with ui.column().classes('w-full'):
                                ui.label('Image').classes('text-lg font-semibold mb-2')
                                if editor.baseimage_path and Path(editor.baseimage_path).exists():
                                    editor.base_image_view = ui.image(editor.baseimage_path).classes('w-full h-96 object-contain')
                                else:
                                    editor.base_image_view = ui.label('No base image selected').classes('text-gray-500 text-center')

                        ui.button('Close', on_click=editor.log_dialog.close).classes('mt-4')
            else:
                # Update image if baseimage path changed
                if editor.baseimage_path and Path(editor.baseimage_path).exists():
                    editor.base_image_view.set_source(editor.baseimage_path)

            # Clear previous log content
            editor.log_output.clear()
            editor.log_dialog.open()

            # Run script with real-time output capture
            async def run_subprocess(prompt_file):
                log_file = prompt_file.replace('.json', '.log')
                if os.path.exists(log_file):
                    os.remove(log_file)

                response_dir = os.path.dirname(prompt_file)
                # delete old image files
                if not use_last_output:
                    if os.path.exists(response_dir):
                        for file in Path(response_dir).glob('test-*.png'):
                            os.remove(file)

                cmd = ['python', 'scriptgen.py',
                       prompt_file,
                       str(minlength),
                       str(maxlength),
                       str(transition),
                       music_hints]
                if use_last_output:
                    response_file = prompt_file.replace('.json', '_response.json')
                    cmd.append(f"--response_file={response_file}")
                if music_enabled:
                    cmd.append('--music_enabled')
                if not run_image_gen:
                    cmd.append('--skip_image_gen')
                if feedback_last_image:
                    cmd.append('--feedback_image')

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                # Read stdout and stderr concurrently
                async def read_stream(stream, is_error=False):
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        text = line.decode('utf-8').rstrip()
                        if text:
                            editor.log_output.push(text)
                            # Write to log file
                            with open(log_file, 'a') as f:
                                f.write(text + '\n')

                # Start file watcher for new PNG files
                async def watch_for_images():
                    seen_files = set()
                    seen_files.add(editor.baseimage_path)
                    seen_files.add(os.path.join(response_dir, 'test-0.png'))

                    while process.returncode is None:
                        try:
                            if os.path.exists(response_dir):
                                for file in Path(response_dir).glob('test-*.png'):
                                    file_str = str(file)
                                    if file_str not in seen_files:
                                        seen_files.add(file_str)
                                        # Update the base image view with the new file
                                        if hasattr(editor, 'base_image_view'):
                                            imageUrl = app.add_media_file(local_file=Path(file_str))
                                            editor.base_image_view.set_source(imageUrl)
                                            editor.log_output.push(f'Updated image view with: {file.name}')
                        except Exception as e:
                            editor.log_output.push(f'Error watching for images: {str(e)}')

                        await asyncio.sleep(0.5)  # Check every 500ms

                # Start the file watcher task
                if not use_last_output:
                    watcher_task = asyncio.create_task(watch_for_images())

                # Wait for both stdout and stderr
                await asyncio.gather(
                    read_stream(process.stdout),
                    read_stream(process.stderr, True),
                )

                await process.wait()

                if process.returncode == 0:
                    ui.notify("Script completed successfully", type="positive")

                    # Close the log window
                    editor.log_output.push('\n✓ Script completed successfully')
                    # Wait for 1 second
                    await asyncio.sleep(4)
                    editor.log_dialog.close()

                    script_folder = os.path.dirname(prompt_file)
                    base_mp4_file, _ = os.path.splitext(prompt_file)
                    mp4_file = os.path.join(script_folder,  base_mp4_file + ".mp4")

                    # Check for test_XX.mp4 files and find the latest one
                    latest_version = -1
                    latest_file = mp4_file

                    pattern = os.path.join(script_folder, f"{base_mp4_file}_*.mp4")

                    for file in glob.glob(pattern, recursive=False):
                        try:
                            # Extract version number from filename
                            stem = Path(file).stem
                            version_str = stem.split('_')[-1]
                            version = int(version_str)
                            if version > latest_version:
                                latest_version = version
                                latest_file = str(file)
                        except (ValueError, IndexError):
                            continue

                    # If we found a versioned file, use it; otherwise use test.mp4
                    mp4_file = latest_file

                    # Open new dialog with video player
                    if Path(mp4_file).exists():
                        mp4Url = app.add_media_file(local_file=Path(mp4_file))
                        with ui.dialog() as video_dialog:
                            with ui.card().classes('w-full max-w-6xl'):
                                ui.label('Generated Video').classes('text-xl font-bold mb-4')
                                ui.video(mp4Url).classes('w-full')
                                ui.button('Close', on_click=video_dialog.close).classes('mt-4')
                        video_dialog.open()
                    else:
                        ui.notify(f"Video file {mp4_file} not found", type="warning")

                else:
                    editor.log_output.push(f'\n✗ Script failed with exit code {process.returncode}')

            prompt_file = editor.load_file_input.value or "prompts.json"

            await run_subprocess(prompt_file)
            ui.notify("Script executed successfully", type="positive")
        except Exception as e:
            ui.notify(f"Error running script: {str(e)}", type="negative")

editor = PromptEditor()

async def pick_file() -> None:
    result = await local_file_picker(editor.rootFolder, multiple=False, show_hidden_files=False)
    if not result or not result[0]:
        ui.notify("No file selected", type="warning")
        return
    ui.notify(f'You chose {result[0]}')
    editor.load_file_input.set_value(result[0])
    editor.load_from_json()

with ui.card().classes("w-full max-w-4xl mx-auto p-6"):
    ui.label("Slideshow Prompt Editor").classes("text-2xl font-bold mb-4")
    # Initialize log window and process tracking
    editor.process = None
    editor.log_content = []

    # Base Prompt
    ui.label("Base Prompt:").classes("text-lg font-semibold mt-4")
    editor.baseprompt_textarea = ui.textarea(
        placeholder="Enter base prompt...",
        on_change=lambda e: setattr(editor, 'baseprompt', e.value)
    ).classes("w-full text-lg").props("rows=12")

    # Prompt
    ui.label("Prompt:").classes("text-lg font-semibold mt-4")
    editor.prompt_textarea = ui.textarea(
        placeholder="Enter prompt...",
        on_change=lambda e: setattr(editor, 'prompt', e.value)
    ).classes("w-full text-lg").props("rows=12")

    # Base Image Prompt
    ui.label("Base Image Prompt:").classes("text-lg font-semibold mt-4")
    editor.base_image_prompt_textarea = ui.textarea(
        placeholder="Enter base image prompt...",
        on_change=lambda e: setattr(editor, 'base_image_prompt', e.value)
    ).classes("w-full text-lg").props("rows=12")

    # File selections
    with ui.row().classes("w-full gap-4 mt-6"):
        with ui.column().classes("flex-1"):
            ui.label("Base Image:").classes("font-semibold")
            editor.baseimage_label = ui.label("No image selected").classes("text-sm text-gray-600")
            async def handle_baseimage_upload(e):
                # Store the uploaded file to a temporary location or specific directory

                # Create a temporary file to store the uploaded content
                # Save to a specific directory with original filename
                upload_dir = Path("uploads")  # You can change this to any directory
                upload_dir.mkdir(exist_ok=True)

                file_path = upload_dir / e.name

                # Handle duplicate filenames if needed
                counter = 1
                while file_path.exists():
                    stem = Path(e.name).stem
                    suffix = Path(e.name).suffix
                    file_path = upload_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(e.content, f)

                full_path = str(file_path.absolute())

                setattr(editor, 'baseimage_path', full_path)
                editor.baseimage_label.set_text(f"Selected: {e.name}")

            ui.upload(
                on_upload=handle_baseimage_upload
            ).props('accept=".jpg,.jpeg,.png,.gif,.bmp"').classes("w-full")

    #
    with ui.row().classes("w-full gap-4 mt-6"):
        with ui.column().classes("flex-1"):
            ui.label("Settings:").classes("font-semibold")
            with ui.row().classes("gap-2"):
                editor.min_length_input = ui.number(
                    label="Min Length (seconds)",
                    value=50,
                    min=1,
                    format='%.0f'
                ).classes("w-32")
                editor.max_length_input = ui.number(
                    label="Max Length (seconds)",
                    value=90,
                    min=1,
                    format='%.0f'
                ).classes("w-32")
                editor.transition_input = ui.number(
                    label="Transition Time (seconds)",
                    value=1.5,
                    min=0.5,
                    step=0.5,
                    precision=1,
                    format='%0.1f',
                ).classes("w-32")
                editor.music_enabled_checkbox = ui.checkbox('Add music', value=True).classes("ml-2")
                editor.feedback_enabled = ui.checkbox('Enable feedback previous image', value=True).classes("ml-2")
                editor.hints_input = ui.textarea(
                    label="Music Generation Hints",
                    placeholder="Enter hints for music generation...",
                    on_change=lambda e: setattr(editor, 'music_hints', e.value)
                ).classes("w-full mt-2").props("rows=3")
                ui.label("Music Genre:").classes("font-semibold mt-2")
                editor.genre_select = ui.select(
                    options=editor.genre_list if hasattr(editor, 'genre_list') else [],
                    label="Select Genre",
                    clearable=True,
                    on_change=lambda e: setattr(editor, 'selected_genre', e.value)
                ).classes("w-full")

    # Buttons
    with ui.row().classes("w-full gap-4 mt-6"):
        # Feedback checkbox
        ui.button("Run", on_click=lambda: editor.run_script(
            use_last_output=False,
            run_image_gen=True)
        ).props("color=primary")

        ui.button("Run (No Images)", on_click=lambda: editor.run_script(
            use_last_output=False,
            run_image_gen=False)
        ).props("color=warning")

        ui.button("Rebuild Last Images and Video", on_click=lambda: editor.run_script(
            use_last_output=True,
            run_image_gen=True)
        ).props("color=secondary")

        ui.button("Rebuild Last Video", on_click=lambda: editor.run_script(
            use_last_output=True,
            run_image_gen=False)
        ).props("color=secondary")

        with ui.row().classes("gap-2"):
            editor.load_file_input = ui.input(
                placeholder="Select JSON file to load..."
            ).props('readonly')
            ui.button('Load Json File', on_click=lambda: pick_file(), icon='folder')
            ui.button("Save", on_click=editor.save_to_json).props("color=secondary")

# need buttons for min/max length of audio, crossfade time, hints for music gen
# need a reprocess response, lets user select a response file and it reruns the imagegen or music selection/video gen

ui.run(title="OpenAI Prompt Editor")

