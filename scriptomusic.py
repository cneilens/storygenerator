import os
import json
import argparse
import datetime
import requests
from openai import OpenAI

client = OpenAI()

CACHE_FILE = 'incompetech_metadata.json'
GENRE_CACHE_FILE = 'incompetech_genre.json'
CACHE_TTL = datetime.timedelta(days=1)
METADATA_URL = 'https://incompetech.com/music/royalty-free/pieces.json'
GENRE_URL = 'https://incompetech.com/music/royalty-free/genre.json'
BASE_MP3_URL = 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/'

def download_metadata(force=False):
    """
    Download and cache Incompetech metadata JSON.
    """
    if not force and os.path.exists(CACHE_FILE):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if datetime.datetime.now() - mtime < CACHE_TTL:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    print("Fetching metadata from Incompetech...")
    resp = requests.get(METADATA_URL)
    resp.raise_for_status()
    data = resp.json()
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return data

def download_genres(force:False):
    """
    Download and cache Incompetech genre JSON.
    """
    if not force and os.path.exists(GENRE_CACHE_FILE):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(GENRE_CACHE_FILE))
        if datetime.datetime.now() - mtime < CACHE_TTL:
            with open(GENRE_CACHE_FILE, 'r') as f:
                return json.load(f)
    print("Fetching genres from Incompetech...")
    resp = requests.get(GENRE_URL)
    resp.raise_for_status()
    data = resp.json()
    with open(GENRE_CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return data


def parse_duration(duration_str):
    """
    Convert duration string 'hh:mm:ss' or 'mm:ss' to seconds.
    """
    parts = list(map(int, duration_str.split(':')))
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h = 0; m, s = parts
    else:
        return 0
    return h * 3600 + m * 60 + s


def analyze_script(script, hints):
    """
    Use OpenAI to recommend mood (feel), bpm, and genre based on script and hints.
    """
    prompt = f"""You are a music recommendation engine specialized in Incompetech music.
Given the following script/storyboard and any additional hints, suggest a musical mood (feel), tempo in BPM (integer), and genre (style) that best matches.

Script:
{script}

Hints:
{hints or ''}

Respond in JSON with keys 'mood', 'bpm', 'genre'."""
    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
        temperature=0.7,
    )
    
    jsonresponse = response.output_text.removeprefix("```json\n")
    jsonresponse = jsonresponse.removesuffix("\n```")
    jsonresponse = jsonresponse.replace("\'", "'")
    
    try:
        rec = json.loads(jsonresponse)
        return rec.get('mood'), rec.get('bpm'), rec.get('genre')
    except Exception:
        print("Warning: could not parse OpenAI response as JSON.")
        return None, None, None


    
def find_track(metadata, mood, bpm, genre, min_len, max_len, hints=None):
    """
    Use OpenAI to recommend search metadatabase for us.
    """
# Convert seconds to HH:MM:SS format
    def seconds_to_timestamp(seconds):
        if not seconds or seconds <= 0:
            return "00:00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    min_len_timestamp = seconds_to_timestamp(min_len) if min_len else 0
    max_len_timestamp = seconds_to_timestamp(max_len) if max_len else 0
        
    prompt = f"""You are a music recommendation engine specialized in Incompetech music.
Given the following metadata database json file, search all the tracks in the database and recommend upto 5 tracks that best match the mood, bpm, genre and any additional hints.
Use the feel, description, instruments and genre fields of the metadata to determine the best matches.
Bias on genre over bpm. 
Also bias using the instruments that better match the genre.
If the passed min_len and max_len are greater than 0, filter the tracks by the length of the track, min_len and max_len are times in seconds. Use the length field in the metadata for filtering by tracklength. 
Only use the lengths as a rough guide, not an exact match. 
But do not return tracks that are less than the min_len if other tracks are available.
Bias genre and mood over length.

metadata:
{json.dumps(metadata, indent=2)}   

mood:
{mood}
bpm:
{bpm}
genre:
{genre}
min_len:
{min_len_timestamp}
max_len:
{max_len_timestamp}
Hints:
{hints or ''}

Purely respond as JSON with an array named 'tracks' which is  the metadata to the best matching tracks  and an object named 'reasoning' that describes your reasoning for selection.
Ensure its valid json without any extra text or formatting.
"""
    print("Finding a track for the script...")
    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
        temperature=0.7,
    )
    
    jsonresponse = response.output_text.removeprefix("```json\n")
    jsonresponse = jsonresponse.removesuffix("\n```")
    jsonresponse = jsonresponse.removesuffix("```")
    jsonresponse = jsonresponse.replace("\'", "'")
    
    try:
        rec = json.loads(jsonresponse)
        return rec
    except Exception as e:
        print(f"Warning: could not parse OpenAI response as JSON. {e}")
        print("Response was:", jsonresponse)
        return None

def download_mp3(track, output_dir='downloads'):
    """
    Stream and save the MP3 file for the selected track.
    """
    if not track:
        return None
    os.makedirs(output_dir, exist_ok=True)
    filename = track['filename']
    url = BASE_MP3_URL + filename
    local_path = os.path.join(output_dir, filename)
    if not os.path.exists(local_path):
        print(f"Downloading {url}...")
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024):
                f.write(chunk)
    else:
        print(f"File {local_path} already exists, skipping download.")
    return local_path

def get_best_track_for_script(script, hints=None, min_length=None, max_length=None, refreshCache=False):
    metadata = download_metadata(force=refreshCache)
    genres = download_genres(force=refreshCache)
    # Convert genres from list to dict mapping index to genre name
    genre_dict = {}
    for genre_item in genres:
        genre_dict[f"{genre_item['id']}"] = genre_item['genre']
    genres = genre_dict
    for data in metadata:
        genre_index = data.get("genre")
        genre_name = genres.get(genre_index)
        data["genre"] = genre_name
    
    mood, bpm, genre = analyze_script(script, hints)
    
    print(f"Recommended mood: {mood}, bpm: {bpm}, genre: {genre}")
    best_tracks = find_track(metadata, mood, bpm, genre, min_length, max_length, hints)
    if best_tracks:
        tracks = best_tracks.get('tracks', [])
        if tracks:
            reasoning = best_tracks.get('reasoning')
            print(f"Reasoning: \n {reasoning}\n")
            track = tracks[0]
            if track:
                print(f"Recommended track: \n {json.dumps(track, indent=2)}\n")
                path = download_mp3(track)
                if path:
                    print("Downloaded:", path)
                    return path
                else:
                    print("Failed to download track.")

    print("No suitable tracks.")
    return None

def main():
    # parser = argparse.ArgumentParser(description='Search and download Incompetech music for a script/storyboard.')
    # parser.add_argument('--script_file', help='Path to script/storyboard text file')
    # parser.add_argument('--script_text', help='Script/storyboard text')
    # parser.add_argument('--hints', help='Additional hints for style of music')
    # parser.add_argument('--min_length', type=int, help='Minimum duration in seconds')
    # parser.add_argument('--max_length', type=int, help='Maximum duration in seconds')
    # parser.add_argument('--refresh_cache', action='store_true', help='Force refresh of metadata cache')
    # args = parser.parse_args()

    # if script_file:
    #     with open(script_file, 'r') as f:
    #         script = f.read()
    # else:
    #     script = script_text or ''
    
    jsonresponse = json.load(open("prompts_response.json", "r"))
    
    script = jsonresponse.get("script")
    hints = ""
    min_length = 40
    max_length = 100
    refresh_cache = False

    get_best_track_for_script(script, hints, min_length, max_length, refresh_cache)
                        

if __name__ == '__main__':
    main()
