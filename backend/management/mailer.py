import logging, json
import asyncio
import sys
sys.path.append("../util")
from util.supabase import supa_connect
from util.r2 import r2_retrieve
from util.mail import publish

def new_transcript(cursor, episode):
    """
    When a new transcript is available, process subscriptions pending on it.
    """
    # Get subscriptions pending on the episode 
    cursor.execute("SELECT * FROM subscriptions WHERE pending_publish_id = %s", [episode['id']])
    subs = cursor.fetchall()

    if len(subs) == 0:
        return
    
    # Get podcast
    cursor.execute("SELECT * from podcasts WHERE id = %s", [episode['podcast_id']])
    podcast = cursor.fetchone()
    
    # Image is episode image if it has one, otherwise podcast image
    if 'image_url' in episode:
        image_url = episode['image_url']
    else:
        image_url = podcast['image_url']
    
    # Get email HTML from R2
    email_html = r2_retrieve(episode['filename'])
    # Subject is <podcast title>: <episode title>
    subject = f"{podcast['title']}: {episode['title']}"

    # publish subscriptions
    for sub in subs:
        # get user email
        cursor.execute("SELECT email FROM auth.users WHERE id = %s", [sub['user_id']])
        email = cursor.fetchone()['email']
        # publish
        publish(to_email=email, subject=subject, body=email_html, image_url=image_url)

def main():
    conn = supa_connect()
    cursor = conn.cursor()
    cursor.execute(f"LISTEN new_transcript;")

    def handle_notify():
        conn.poll()
        for notify in conn.notifies:
            episode = json.loads(notify.payload)['record']
            logging.info(f"New transcript for episode: {episode['id']}")
            new_transcript(cursor=cursor, episode=episode)
        conn.commit()
        conn.notifies.clear()

    logging.info("Listening for Supabase new_transcript notifications!")
    loop = asyncio.get_event_loop()
    loop.add_reader(conn, handle_notify)
    loop.run_forever()

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
