import asyncio
import json, logging
from db import connect
from supabase import supa_connect, handle_new_user
from storage import import_user_sub
from dotenv import dotenv_values
env = dotenv_values('.env.local')

"""
Listens to the postgres user_verified notification channel to process new users.
"""

def main():
    # dbname should be the same for the notifying process
    conn = supa_connect()
    cursor = conn.cursor()
    cursor.execute(f"LISTEN user_verified;")

    def handle_notify():
        conn.poll()
        for notify in conn.notifies:
            logging.info(f"Got db notify: {notify.payload}")
            data = json.loads(notify.payload)['record']
            with connect() as my_connection:
                handle_new_user(my_connection, data)
        conn.notifies.clear()

    # It works with uvloop too:
    # import uvloop
    # loop = uvloop.new_event_loop()
    # asyncio.set_event_loop(loop)

    loop = asyncio.get_event_loop()
    loop.add_reader(conn, handle_notify)
    loop.run_forever()

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
    # payload = '{"record" : {"id":"9bf31800-3c12-4f15-8d78-9e3e4b3d8792","email":"costes.c@gmail.com","raw_user_meta_data":{"user_metadata": {"podcast": {"apple_id": 1200361736, "feed_url": "https://feeds.simplecast.com/54nAGcIl"}}},"token":"2c3318f9-5cc1-47fe-bbf2-4321b0cd7c36"}}'
    # data = json.loads(payload)['record']
    # handle_new_user(data)
