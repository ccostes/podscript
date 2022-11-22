import logging, json
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
from util.supabase import supa_connect

def main():
    conn = supa_connect()
    cursor = conn.cursor()
    cursor.execute(f"LISTEN new_transcript;")

    def handle_notify():
        conn.poll()
        for notify in conn.notifies:
            episode = json.loads(notify.payload)['record']
            if episode.get('filename') is not None and episode['filename'] != '':
                logging.info(f"Processing new transcript for episode: {episode['id']}")
                new_transcript(cursor=cursor, episode=episode)
        conn.commit()
        conn.notifies.clear()

    logging.info("Listening for Supabase new_transcript notifications!")
    loop = asyncio.new_event_loop()
    loop.add_reader(conn, handle_notify)
    loop.run_forever()

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
