import asyncio
import json, logging
import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
from util.supabase import supa_connect
from feeds import update_feed

def main():
    conn = supa_connect()
    cursor = conn.cursor()
    cursor.execute(f"LISTEN new_podcast;")

    def handle_notify():
        conn.poll()
        for notify in conn.notifies:
            podcast = json.loads(notify.payload)['record']
            update_feed(cursor=cursor, podcast=podcast)
        conn.commit()
        conn.notifies.clear()

    logging.info("Listening for Supabase new_podcast notifications!")
    loop = asyncio.new_event_loop()
    loop.add_reader(conn, handle_notify)
    loop.run_forever()

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
