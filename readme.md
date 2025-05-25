# AI Comic & Slideshow Generation Suite

A collection of Python scripts and modules for:

- **Editing and managing OpenAI prompts** in a web UI  
- **Generating stories** (JSON) and **slideshow videos** with transitions and background music  
- **Analyzing audio** to time slideshow transitions  
- **Downloading royalty-free tracks** from Incompetech to match your script  
- **Creating AI-driven comics** and exporting them as PDFs

The **main entry point** is `scriptgen_editor.py`, which brings up a NiceGUI web app for composing and running your prompts.

---

## 📝 Prompt Editor & Script Generation

### `scriptgen_editor.py`  
– **Main UI**: launches a NiceGUI app where you can edit three prompts (`baseprompt`, `prompt`, `base_image_prompt`), upload a base image and an MP3, save/load JSON, and run the full pipeline.  
– **Run action**: saves `prompts.json` and invokes `scriptgen.py prompts.json`, streaming logs back into the browser.

### `scriptgen.py`  
– **Reads** the JSON prompts file, calls the OpenAI API to generate a story JSON (`<story_file>.json`).  
– **Downloads** the base image and any generated “test-*.png” images.  
– **Selects** a music track via `scriptomusic.get_best_track_for_script()`.  
– **Calls** `automoviegen.create_slideshow()` to produce the final MP4 video.

---

## 🎵 Audio & Music Selection

### `scriptomusic.py`  
– **Fetches and caches** Incompetech metadata and genre data.  
– **Analyzes** your script text (plus optional hints) for mood, BPM, and genre.  
– **Chooses** the best matching track within your length constraints and downloads the MP3.

### `musicanalyzer.py`  
– **Uses Librosa** to load an audio file, detect tempo, beat frames, and RMS energy.  
– **Computes** natural transition points (start times, durations, and transition lengths) for a given number of slides.  
– **Returns** a JSON-style dict: `{ "tempo":…, "slides":[{ slide, start, duration, transition }, …] }`.

---

## 🎥 Video Slideshow Generation

### `automoviegen.py`  
– **High-level slideshow builder**:  
  - Resizes and pads images (blurred borders for portrait)  
  - Arranges clips using timings from `musicanalyzer`  
  - Applies crossfades or other transitions (from `transitions.py`)  
  - Overlays background music (if provided)  
  - Exports an MP4 via MoviePy

### `moviegen.py`  
– **Simpler slideshow script** (without advanced audio analysis):  
  - Resizes images to common height  
  - Applies a selectable set of wipe/fade transitions  
  - Combines with a single audio track  

---

## 🔄 Video Transition Effects

### `transitions.py`  
A library of custom MoviePy transition functions, including:

- **Wipes** (left, right, up, down, door, circle, diamond, clock, luma wipe)  
- **Slides** (push, split-screen, Venetian blinds, checkerboard)  
- **Zoom**, **rotate**, **flip**  
- **Blur**, **pixel dissolve**, **burn**, **ripple**, **flash**, **glitch**  
- **`apply_transition(clip1, clip2, name, …)`** to pick transitions by name

---

## 📚 Comic Book Generation

### `comicgenerator.py`  
– **Loads** a JSON spec (`superhero-comic.json`) for a base image and a sequence of “comic” panels.  
– **Calls** the OpenAI Image Edit API (`gpt-image-1`) to turn each panel into a photo-realistic version.  
– **Collects** the generated PNGs and compiles them into a multi-page PDF via Pillow.

---

## 🚀 Getting Started

1. **Install** Python 3.8+ and clone this repo.  
2. **Create a virtual environment** (recommended):  
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies** 
    ```bash
    pip install -r requirements.txt
    ```
4. **Launch the prompt editor**
    ```bash
    python3 scriptgen_editor.py
    ```
5. **Compose your prompts**, upload a base image and MP3, then click Run to generate story JSON, images, music, and a final slideshow.
All heavy lifting (AI calls, audio analysis, video editing) is modularized—feel free to mix and match the scripts for your own pipelines!
