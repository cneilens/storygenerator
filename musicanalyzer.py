import librosa
import numpy as np
import json

def _select_best_spaced_points(candidates, n_points, total_duration):
    """Select n_points from candidates with optimal spacing."""
    if n_points >= len(candidates):
        return np.arange(len(candidates))
    
    ideal_spacing = total_duration / (n_points + 1)
    n_candidates = len(candidates)
    
    # Dynamic programming to find best selection
    dp = {}
    
    def score(indices):
        if len(indices) < 2:
            return 0
        spacings = np.diff(candidates[indices])
        return -np.sum((spacings - ideal_spacing) ** 2)
    
    # Greedy approximation for efficiency
    selected = [0]  # Start with first candidate
    for _ in range(n_points - 1):
        best_next = -1
        best_score = -np.inf
        for i in range(selected[-1] + 1, n_candidates):
            temp_selected = selected + [i]
            temp_score = score(np.array(temp_selected))
            if temp_score > best_score:
                best_score = temp_score
                best_next = i
        if best_next >= 0:
            selected.append(best_next)
    
    return np.array(selected)

def find_transition_points(filename, num_slides, transition_duration=1.5, fade_duration=3.0):
    """
    Find optimal transition points in music based on rhythm, beats, and musical changes.
    
    Args:
        filename: Path to audio file
        num_slides: Number of slides to transition between
        transition_duration: Duration of transitions between slides (seconds)
        fade_duration: Duration of fade to black for final slide (seconds)
    
    Returns:
        List of transition start times in seconds
    """
    y, sr = librosa.load(filename, sr=None)
    
    # Get multiple musical features for better transition detection
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)
    
    # Onset strength for detecting musical changes
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    
    # Spectral contrast for timbral changes
    spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    spectral_change = np.diff(np.mean(spectral_contrast, axis=0))
    
    # Combine features into a single novelty curve
    onset_norm = onset_env / np.max(onset_env) if np.max(onset_env) > 0 else onset_env
    spectral_norm = np.abs(spectral_change) / np.max(np.abs(spectral_change)) if np.max(np.abs(spectral_change)) > 0 else spectral_change
    
    # Pad spectral_norm to match onset_env length
    spectral_norm = np.pad(spectral_norm, (0, len(onset_norm) - len(spectral_norm)), mode='constant')
    
    # Combined novelty function
    novelty = 0.6 * onset_norm + 0.4 * spectral_norm
    
    # Find peaks in the combined novelty function
    peaks = librosa.util.peak_pick(novelty, pre_max=10, post_max=10, 
                                   pre_avg=10, post_avg=10, delta=0.2, wait=20)
    
    # Convert to time
    frame_times = librosa.frames_to_time(np.arange(len(novelty)), sr=sr)
    peak_times = frame_times[peaks]
    
    # Add beats that coincide with high novelty
    beat_novelty_threshold = np.percentile(novelty, 70)
    significant_beats = []
    for beat_time in beat_times:
        closest_frame = np.argmin(np.abs(frame_times - beat_time))
        if novelty[closest_frame] > beat_novelty_threshold:
            significant_beats.append(beat_time)
    
    # Combine all candidate points
    all_candidates = np.unique(np.concatenate([peak_times, significant_beats]))
    all_candidates = np.sort(all_candidates)
    
    # Select num_slides points with good spacing
    duration = librosa.get_duration(y=y, sr=sr)
    if len(peak_times) > num_slides + 1:
        # Use dynamic programming to find best spaced points
        print("using dynamic programming to select best spaced points")
        selected_indices = _select_best_spaced_points(all_candidates, num_slides+1, duration)
        transition_points = all_candidates[selected_indices]
    else:
        # Fall back to evenly spaced if not enough candidates
        print("not enough candidates, using evenly spaced points")
        transition_points = np.linspace(duration / (num_slides + 1), 
                                      duration - fade_duration, num_slides+1)
    
    transition_points = transition_points.tolist()
    print(f"Transition points: {len(transition_points)}")
    print(f"NumSlides: {num_slides}")
    # Build slide JSON with timings
    slides = []
    for i in range(num_slides):
        start = float(transition_points[i])
        end = float(transition_points[i + 1])
        duration = end - start - transition_duration if i < num_slides - 1 else end - start - fade_duration
        duration = max(duration, 0.5)  # Ensure minimum visible duration
        slides.append({
            "slide": i + 1,
            "start": round(start, 2),
            "duration": round(duration, 2),
            "transition": transition_duration if i < num_slides - 1 else fade_duration
        })

    return {"tempo": tempo, "slides": slides}
    

def analyze_audio(filename, num_slides, transition_duration=1.5, fade_duration=3.0):
    """
    Analyze audio file to determine slide transitions based on rhythm and musical changes.
    
    Args:
        filename: Path to audio file
        num_slides: Number of slides to transition between
        transition_duration: Duration of transitions between slides (seconds)
        fade_duration: Duration of fade to black for final slide (seconds)
    """
    return find_transition_points(filename, num_slides, transition_duration=transition_duration, fade_duration=fade_duration)


# Example usage
if __name__ == "__main__":
    # audio_file = sys.argv[1]
    # num_slides = int(sys.argv[2])
    result_json = analyze_audio("music/cherry-stone-rock-205899.mp3", 17)
    print(result_json)
    json.dump(result_json, open("slide_transitions.json", "w"), indent=4)