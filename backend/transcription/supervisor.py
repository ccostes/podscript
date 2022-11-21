from signal import SIGINT, SIGTERM
import logging, json, requests, subprocess
from urllib.parse import urlparse, unquote
from os.path import splitext
import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
from util.r2 import r2_upload
from util.supabase import supa_connect
from transcribe import transcribe
from generate_email import generate_email

storage_dir = Path("C:\\Users\\coste\\podscript_data")

def get_ext(url):
    """Return the filename extension from url, or ''."""
    parsed = urlparse(url)
    root, ext = splitext(parsed.path)
    return ext  # or ext[1:] if you don't want the leading '.'

def download_file(url, dst_path):
    uri = urlparse(url)
    filepath = dst_path  / unquote(Path(uri.path).name)
    if filepath.is_file():
        return filepath
    r = requests.get(url, allow_redirects=True)
    with open(filepath, 'wb') as f:
        f.write(r.content)
    return filepath

def process_episode(cursor, file_prefix, episode):
    """
    Run the transcription pipeline for each new episode.
    """
    logging.info("Processing episode...")
    path = storage_dir / file_prefix
    path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Storage dir: {path}")

    # download and convert audio file
    audio_filepath = download_file(url=episode['episode_url'], dst_path=path)
    logging.info(f"Downloaded audio file {audio_filepath}")
    if audio_filepath.suffix != '.wav':
        wav_filepath = audio_filepath.with_suffix('.wav')
        if not wav_filepath.is_file():
            logging.info(f"Converting audio file {audio_filepath} to {wav_filepath}")
            subprocess.call(['ffmpeg', '-i', audio_filepath, wav_filepath, '-y'])
        audio_filepath = wav_filepath
    
    # Generate transcription data
    transcript_filepath = (path / 'transcript.json')
    if not transcript_filepath.is_file():
        logging.info("Transcribing episode...")
        transcript = transcribe(filename=str(audio_filepath))
        # Save transcript data as json
        with transcript_filepath.open('w') as f:
            json.dump(transcript, f)
    else:
        with transcript_filepath.open() as f:
            transcript = json.loads(f.read())
    
    # Upload transcript json
    id = f"{episode['published'].strftime('%Y-%m-%d_%H-%M-%S')}_{episode.get('guid')}"
    r2_id = str((Path() / file_prefix / id).as_posix()) + '.json'
    logging.info(f"Uploading file {r2_id}...")
    r2_upload(file_path=str(transcript_filepath), id=r2_id)
    
    # Generate email
    # email_path = path / 'email.html'
    # if not email_path.is_file():
    #     logging.info("Generating email...")
    #     if episode.get('image_url') is not None:
    #         image_extension = get_ext(episode['image_url'])
    #         logging.info(f"Using episode image ({episode['image_url']}) extension: {image_extension}")
    #     else:
    #         image_extension = get_ext(episode['podcast_image_url'])
    #         logging.info(f"Using podcast image ({episode['podcast_image_url']}) extension: {image_extension}")
    #     email = generate_email(episode=episode, image_extension=image_extension, transcript=transcript)
    #     # Save email
    #     email_path.write_text(email)

    #     # Upload email file
    #     id = f"{episode['published'].strftime('%Y-%m-%d_%H-%M-%S')}_{episode.get('guid')}"
    #     r2_id = str((Path() / file_prefix / id).as_posix()) + '.html'
    #     logging.info(f"Uploading file {r2_id}...")
    #     r2_upload(file_path=str(email_path), id=r2_id)

    #     # Update episode record with email file id
    #     logging.info("Updating episode record...")
    #     cursor.execute("UPDATE episodes SET filename = %s WHERE id = %s", [r2_id, episode['id']])

import time
def main():
    conn = supa_connect()
    cursor = conn.cursor()
    while True:
        cursor.execute("""
        SELECT ep.id, ep.title, ep.description, ep.description_html, ep.episode_url,
        ep.published, ep.guid, ep.link, ep.filename, ep.image_url,
        pod.image_url as podcast_image_url, pod.file_prefix
        FROM episodes as ep 
        JOIN podcasts AS pod ON pod.id = podcast_id
        WHERE filename IS NULL
        """)
        queue = cursor.fetchall()
        for ep in queue:
            print(f"Episode: {ep}")
            process_episode(cursor=cursor, file_prefix=ep['file_prefix'], episode=ep)
        time.sleep(10)
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
    # transcribe(cursor=None, podcast={
    #     'file_prefix': '140'
    # },
    # episode={

    # })
