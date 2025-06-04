# Music Slideshow Analyzer

Analyzes MP3 files to create synchronized slideshow timing based on musical features.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python analyze_music_slideshow.py music.mp3 --num-slides 10 --transition-time 1.5 --fade-out-time 2.0
```

## Parameters

- `mp3_file`: Path to the MP3 file to analyze
- `--num-slides`: Number of slides in the slideshow
- `--transition-time`: Duration of transitions between slides (seconds)
- `--fade-out-time`: Duration of the final fade to black (seconds)
- `--output`: Optional output file for JSON results

## Output Format

```json
{
  "slides": [
    {
      "duration": 5.234,
      "transition": 1.5
    }
  ],
  "total_duration": 120.5,
  "detected_tempo": 128.0
}
```

## How It Works

1. **Beat Detection**: Identifies rhythmic beats in the music
2. **Onset Detection**: Finds when new sounds or instruments begin
3. **Spectral Analysis**: Detects major tonal changes
4. **Transition Selection**: Intelligently selects musically appropriate transition points
5. **Timing Calculation**: Ensures slideshow exactly matches audio duration
