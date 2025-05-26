#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
from nicegui import ui
import asyncio
import shutil
import tempfile

class PromptEditor:
    def __init__(self):
        self.baseprompt = ""
        self.prompt = ""
        self.base_image_prompt = ""
        self.baseimage_path = ""
        self.music_path = ""
        # Load prompts.json on startup if it exists
        if Path("prompts.json").exists():
            try:
                with open("prompts.json", "r") as f:
                    data = json.load(f)
                self.baseprompt = data.get("baseprompt", "")
                self.prompt = data.get("prompt", "")
                self.base_image_prompt = data.get("base_image_prompt", "")
                self.baseimage_path = data.get("baseImage", "")
                self.music_path = data.get("music", "")
            except Exception as e:
                print(f"Error loading prompts.json on startup: {str(e)}")
            
    async def save_to_json(self):
        # Return a future that completes when dialog is closed
        loop = asyncio.get_running_loop()
        closed = loop.create_future()
        
        # Create a dialog for filename input
        with ui.dialog() as save_dialog, ui.card():
            ui.label('Save Prompts').classes('text-lg font-bold mb-4')
            
            filename_input = ui.input(
                label='Filename',
                placeholder='Enter filename (without .json extension)',
                value='prompts'
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
                    
                    editor.load_file_input.set_value(filename)
                    data = {
                        "baseprompt": self.baseprompt,
                        "prompt": self.prompt,
                        "base_image_prompt": self.base_image_prompt,
                        "baseImage": self.baseimage_path,
                        "music": self.music_path
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
            self.music_path = data.get("music", "")
            
            self.baseimage_label.text = f"Selected: {Path(self.baseimage_path).name}" if self.baseimage_path else "No image selected"
            self.music_label.text = f"Selected: {Path(self.music_path).name}" if self.music_path else "No music selected"
            
            ui.notify(f"Loaded from {file_path}", type="positive")
        except Exception as e:
            ui.notify(f"Error loading file: {str(e)}", type="negative")
            
    async def run_script(self):
        await self.save_to_json()
        
        try:
            # Create log window if it doesn't exist
            if not hasattr(editor, 'log_window'):
                with ui.dialog() as editor.log_window:
                    with ui.card().classes('w-full max-w-4xl'):
                        ui.label('Script Output').classes('text-xl font-bold mb-4')
                        editor.log_output = ui.log(max_lines=1000).classes('w-full h-96')
                        ui.button('Close', on_click=editor.log_window.close)
            
            # Clear previous log content
            editor.log_output.clear()
            editor.log_window.open()
            
            # Run script with real-time output capture
            async def run_subprocess(prompt_file, mp4_file):

                # if Path(mp4_file).exists():
                #     with ui.dialog() as video_dialog:
                #         with ui.card().classes('w-full max-w-4xl'):
                #             ui.label('Generated Video').classes('text-xl font-bold mb-4')
                #             ui.video(str(mp4_file)).classes('w-full')
                #             ui.button('Close', on_click=video_dialog.close).classes('mt-4')
                #     video_dialog.open()
            
                process = await asyncio.create_subprocess_exec(
                    'python', 'scriptgen.py', prompt_file,
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
                            #   editor.log_output.scroll_to_bottom()
                            # editor.log_output.refresh()
                
                # Wait for both stdout and stderr
                await asyncio.gather(
                    read_stream(process.stdout),
                    read_stream(process.stderr, True)
                )
                
                await process.wait()
                
                if process.returncode == 0:
                    ui.notify("Script completed successfully", type="positive")
                    
                    # Close the log window
                    editor.log_output.push('\n✓ Script completed successfully')
                    editor.log_output.push(f'\n📹 Generated video: {mp4_file}')
                    editor.log_window.close()
                    
                    # Open new dialog with video player
                    if Path(mp4_file).exists():
                        with ui.dialog() as video_dialog:
                            with ui.card().classes('w-full max-w-4xl'):
                                ui.label('Generated Video').classes('text-xl font-bold mb-4')
                                ui.video(mp4_file).classes('w-full')
                                ui.button('Close', on_click=video_dialog.close).classes('mt-4')
                        video_dialog.open()
                    else:
                        ui.notify(f"Video file {mp4_file} not found", type="warning")
                   
                else:
                    editor.log_output.push(f'\n✗ Script failed with exit code {process.returncode}')

            prompt_file = editor.load_file_input.value or "prompts.json"
            mp4_file = prompt_file.replace('.json', '.mp4')
            await run_subprocess(prompt_file, mp4_file)
            ui.notify("Script executed successfully", type="positive")
        except Exception as e:
            ui.notify(f"Error running script: {str(e)}", type="negative")

editor = PromptEditor()

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
    ).classes("w-full").props("rows=8")
    
    # Prompt
    ui.label("Prompt:").classes("text-lg font-semibold mt-4")
    editor.prompt_textarea = ui.textarea(
        placeholder="Enter prompt...",
        on_change=lambda e: setattr(editor, 'prompt', e.value)
    ).classes("w-full").props("rows=8")
    
    # Base Image Prompt
    ui.label("Base Image Prompt:").classes("text-lg font-semibold mt-4")
    editor.base_image_prompt_textarea = ui.textarea(
        placeholder="Enter base image prompt...",
        on_change=lambda e: setattr(editor, 'base_image_prompt', e.value)
    ).classes("w-full").props("rows=8")
    
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
            
        with ui.column().classes("flex-1"):
            ui.label("Music File:").classes("font-semibold")
            editor.music_label = ui.label("No music selected").classes("text-sm text-gray-600")
            async def handle_music_upload(e):
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
                
                setattr(editor, 'music_path', full_path)
                editor.music_label.set_text(f"Selected: {e.name}")
            
            ui.upload(
                on_upload=handle_music_upload
            ).props('accept=".mp3"').classes("w-full")
    
    # Buttons
    with ui.row().classes("w-full gap-4 mt-6"):
        ui.button("Run", on_click=editor.run_script).props("color=primary")
        
        ui.button("Save", on_click=editor.save_to_json).props("color=secondary")
        
        with ui.row().classes("gap-2"):
            editor.load_file_input = ui.input(
                placeholder="Select JSON file to load..."
            ).props('readonly')
            ui.upload(
                on_upload=lambda e: (
                    editor.load_file_input.set_value(e.name),
                    editor.load_from_json()
                ),
                label='Load JSON'
            ).props('accept=".json"').classes("w-32")

ui.run(title="OpenAI Prompt Editor")

