import logging, json
import asyncio
import sys
sys.path.append("../util")
from util.r2 import r2_upload
from util.supabase import supa_connect

def transcribe(cursor, episode):
    """
    Run the transcription pipeline for each new episode.
    """
    logging.info("Transcribing episode...")


def main():
    conn = supa_connect()
    cursor = conn.cursor()
    cursor.execute(f"LISTEN new_episode;")

    def handle_notify():
        conn.poll()
        for notify in conn.notifies:
            episode = json.loads(notify.payload)['record']
            logging.info(f"Transcribing new episode: {episode['id']}")
            transcribe(cursor=cursor, episode=episode)
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
    main()
