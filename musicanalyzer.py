import librosa
import numpy as np
import json


def analyze_audio(filename, num_slides, transition_duration=1.5):
    y, sr = librosa.load(filename, sr=None)

    # Calculate tempo and beats
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Calculate energy (RMS)
    rms = librosa.feature.rms(y=y)[0]
    rms_times = librosa.times_like(rms, sr=sr)

    # Calculate novelty function (onset strength)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    novelty_times = librosa.times_like(onset_env, sr=sr)

    # Detect peaks in the onset strength to find possible transitions
    peak_indices = librosa.util.peak_pick(onset_env, pre_max=5, post_max=5, pre_avg=5, post_avg=5, delta=0.1, wait=10)
    peak_times = novelty_times[peak_indices]

    # Add first and last time to ensure full coverage
    peak_times = np.concatenate(([0.0], peak_times, [librosa.get_duration(y=y, sr=sr)]))

    # If there are more transitions than slides, reduce using linear spacing
    if len(peak_times) > num_slides + 1:
        indices = np.linspace(0, len(peak_times) - 1, num_slides + 1, dtype=int)
        peak_times = peak_times[indices]
    else:
        # If too few transitions, linearly interpolate
        peak_times = np.linspace(0, librosa.get_duration(y=y, sr=sr), num_slides + 1)

    # Build slide JSON with timings
    slides = []
    for i in range(num_slides):
        start = float(peak_times[i])
        end = float(peak_times[i + 1])
        duration = end - start - transition_duration if i < num_slides - 1 else end - start - 3.0
        duration = max(duration, 0.5)  # Ensure minimum visible duration
        slides.append({
            "slide": i + 1,
            "start": round(start, 2),
            "duration": round(duration, 2),
            "transition": transition_duration if i < num_slides - 1 else 3.0
        })

    return {"tempo": tempo, "slides": slides}


# Example usage
if __name__ == "__main__":
    # audio_file = sys.argv[1]
    # num_slides = int(sys.argv[2])
    result_json = analyze_audio("music/cherry-stone-rock-205899.mp3", 17)
    print(result_json)
    json.dump(result_json, open("slide_transitions.json", "w"), indent=4)