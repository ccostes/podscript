import logging, json, requests
from urllib.parse import urlparse, unquote
from pathlib import Path
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
from util.r2 import r2_upload
from util.supabase import supa_connect
from transcribe import transcribe
from generate_email import generate_email

storage_dir = Path("C:\\Users\\coste\\podscript_data")

def download_file(url, dst_path):
    uri = urlparse(url)
    filepath = dst_path  / unquote(Path(uri.path).name)
    r = requests.get(url, allow_redirects=True)
    with open(filepath, 'wb') as f:
        f.write(r.content)
    return filepath

def transcribe(cursor, podcast, episode):
    """
    Run the transcription pipeline for each new episode.
    """
    logging.info("Transcribing episode...")
    path = storage_dir / podcast['file_prefix']
    path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Storage dir: {path}")

    # download audio file
    audio_file = download_file(url=episode['episode_url'], dst_path=path)
    logging.info(f"Downloaded audio file {audio_file}")

    # Generate transcription data
    transcript = transcribe(filename=audio_file)
    # Save transcript data as json
    with (path / 'transcript.json').open('w') as f:
        json.dump(transcript, f)

    # Generate email
    email = generate_email(episode=episode, transcript=transcript)
    # Save email
    email_path = path / 'email.html'
    email_path.write_text(email)

    # Upload email
    id = f"{episode['published'].strftime('%Y-%m-%d_%H-%M-%S')}_{episode.get('guid')}"
    r2_id = Path() / podcast['file_prefix'] / id
    r2_upload(file_path=str(email_path), id=r2_id)

def main():
    conn = supa_connect()
    cursor = conn.cursor()
    cursor.execute(f"LISTEN new_episode;")

    def handle_notify():
        conn.poll()
        for notify in conn.notifies:
            episode = json.loads(notify.payload)['episode']
            podcast = json.loads(notify.payload)['podcast']
            logging.info(f"Transcribing new episode: {episode['id']}")
            transcribe(cursor=cursor, podcast=podcast, episode=episode)
        conn.commit()
        conn.notifies.clear()

    logging.info("Listening for Supabase new_episode notifications!")
    loop = asyncio.get_event_loop()
    loop.add_reader(conn, handle_notify)
    loop.run_forever()

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    # main()
    transcribe(cursor=None, podcast={
        'file_prefix': '140'
    },
    episode={

    })
