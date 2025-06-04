import librosa
import numpy as np
import json
import argparse
import sys

def analyze_music_transitions(audio_path, num_slides, transition_time, fade_out_time):
    """
    Analyze music file and generate slideshow timing based on musical features.
    """
    # Load audio file
    y, sr = librosa.load(audio_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)
    
    # Detect beats and tempo
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)
    
    # Detect onsets (new sounds/instruments)
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    
    # Detect spectral rolloff for major transitions
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    rolloff_delta = np.diff(spectral_rolloff)
    rolloff_peaks = np.where(np.abs(rolloff_delta) > np.std(rolloff_delta) * 2)[0]
    rolloff_times = librosa.frames_to_time(rolloff_peaks, sr=sr)
    
    # Combine all transition points
    all_transitions = np.unique(np.concatenate([
        beat_times[::4],  # Every 4th beat
        onset_times,
        rolloff_times
    ]))
    
    # Filter out transitions that are too close together
    min_slide_duration = transition_time + 1.0  # Minimum 1 second display time
    filtered_transitions = [0]  # Start at beginning
    for t in all_transitions:
        if t - filtered_transitions[-1] >= min_slide_duration:
            filtered_transitions.append(t)
    
    # Ensure we have enough transition points for all slides
    if len(filtered_transitions) < num_slides:
        # Add evenly spaced transitions
        available_duration = duration - fade_out_time
        interval = available_duration / num_slides
        filtered_transitions = [i * interval for i in range(num_slides)]
    elif len(filtered_transitions) > num_slides:
        # Select the most evenly distributed transitions
        indices = np.linspace(0, len(filtered_transitions) - 1, num_slides, dtype=int)
        filtered_transitions = [filtered_transitions[i] for i in indices]
    
    # Calculate slide durations
    slides = []
    min_last_slide_duration = 2.0  # Minimum 2 seconds for last slide
    
    for i in range(num_slides):
        if i < num_slides - 1:
            # Regular slide
            start_time = filtered_transitions[i]
            end_time = filtered_transitions[i + 1] if i + 1 < len(filtered_transitions) else duration
            slide_duration = end_time - start_time - transition_time
            
            slides.append({
                "duration": round(slide_duration, 3),
                "transition": round(transition_time, 3)
            })
        else:
            # Last slide with fade out
            start_time = filtered_transitions[i]
            remaining_time = duration - start_time
            slide_duration = remaining_time - fade_out_time
            
            # Ensure minimum duration for last slide
            if slide_duration < min_last_slide_duration:
                # Need to adjust previous slides to make room
                shortage = min_last_slide_duration - slide_duration
                
                # Redistribute the shortage across previous slides
                if num_slides > 1:
                    reduction_per_slide = shortage / (num_slides - 1)
                    for j in range(len(slides)):
                        slides[j]["duration"] = round(slides[j]["duration"] - reduction_per_slide, 3)
                
                slide_duration = min_last_slide_duration
            
            slides.append({
                "duration": round(slide_duration, 3),
                "transition": round(fade_out_time, 3)
            })
    
    # Verify total duration matches
    total_slideshow_duration = sum(s["duration"] + s["transition"] for s in slides)
    if abs(total_slideshow_duration - duration) > 0.01:
        # Small adjustment to last slide to ensure exact match
        adjustment = duration - total_slideshow_duration
        slides[-1]["duration"] = round(slides[-1]["duration"] + adjustment, 3)
    
    return {
        "slides": slides,
        "total_duration": round(duration, 3),
        #"detected_tempo": round(tempo, 1)
    }

def main():
    parser = argparse.ArgumentParser(description='Analyze MP3 for slideshow timing')
    parser.add_argument('mp3_file', help='Path to MP3 file')
    parser.add_argument('--num-slides', type=int, required=True, help='Number of slides')
    parser.add_argument('--transition-time', type=float, required=True, help='Transition time in seconds')
    parser.add_argument('--fade-out-time', type=float, required=True, help='Fade out time in seconds')
    parser.add_argument('--output', help='Output JSON file (optional)')
    
    args = parser.parse_args()
    
    try:
        # Analyze the music
        result = analyze_music_transitions(
            args.mp3_file,
            args.num_slides,
            args.transition_time,
            args.fade_out_time
        )
        
        # Output JSON
        json_output = json.dumps(result, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"Results saved to {args.output}")
        else:
            print(json_output)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
