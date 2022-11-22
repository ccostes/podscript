import logging, json
from urllib.parse import urlparse
from os.path import splitext
import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
from util.r2 import r2_retrieve
from util.mail import publish
from generate_email import generate_body

def get_ext(url):
    """Return the filename extension from url, or ''."""
    parsed = urlparse(url)
    root, ext = splitext(parsed.path)
    return ext  # or ext[1:] if you don't want the leading '.'

def publish_episode(cursor, episode, subscriptions):
    """
    Publish an episode to the list of subscriptions.
    """
    if len(subscriptions) == 0:
        return
    logging.info(f"Publishing episode {episode['id']} for {len(subscriptions)} subscriptions")
    # Get podcast
    cursor.execute("SELECT * from podcasts WHERE id = %s", [episode['podcast_id']])
    podcast = cursor.fetchone()
    
    # Just use podcast feed image - episode images are too inconsistent 
    image_url = podcast['image_url']

    # Get email HTML from R2
    transcript_json = r2_retrieve(episode['filename'])
    transcript = json.loads(transcript_json)
    email_html = generate_body(
        episode=episode,
        image_extension=get_ext(image_url),
        transcript=transcript,
        preview=episode.get('description')[:120] + '…',
        rights=podcast.get('rights') if 'rights' in podcast and podcast['rights'] is not None else "© " + podcast['author'],
    )
    # Subject is <podcast title>: <episode title>
    subject = f"{podcast['title']}: {episode['title']}"

    # publish subscriptions
    count = 0
    for sub in subscriptions:
        # get user email
        cursor.execute("SELECT email FROM auth.users WHERE id = %s", [sub['user_id']])
        email = cursor.fetchone()['email']
        # publish
        publish(to_email=email, subject=subject, body=email_html, image_url=image_url)
        # Update sub
        cursor.execute("""UPDATE subscriptions as sub SET
            last_published = (SELECT published FROM episodes WHERE id = pending_publish_id),
            last_published_id = pending_publish_id,
            last_published_guid = (SELECT guid FROM episodes WHERE id = pending_publish_id),
            pending_publish_id = COALESCE ((SELECT id from episodes as ep
                where ep.podcast_id = sub.podcast_id 
                and ep.published > (SELECT published FROM episodes WHERE id = sub.pending_publish_id)
                order by published ASC LIMIT 1))
            WHERE id = %s""",
            [sub['id']])
        count += 1
    logging.info(f"Published to {count} subscriptions")

def new_transcript(cursor, episode):
    """Called when a new transcript file has been added to an episode."""
    # Get subscriptions pending on the episode 
    cursor.execute("SELECT * FROM subscriptions WHERE pending_publish_id = %s", [episode['id']])
    subs = cursor.fetchall()
    if len(subs) > 0:
        logging.info(f"{len(subs)} subscriptions pending on episode, publishing...")
        publish_episode(cursor=cursor, episode=episode, subscriptions=subs)

def poll_pending_subs(cursor):
    cursor.execute("""SELECT * FROM subscriptions
        WHERE pending_publish_id IS NOT NULL 
        AND (SELECT filename FROM episodes WHERE id = pending_publish_id) IS NOT NULL""")
    subs = cursor.fetchall()
    if len(subs) > 0:
        logging.info(f"Found {len(subs)} pending subscriptions ready to be published!")
        # Process by episode, first collect into separate lists by episode ID
        by_episode = {}
        for s in subs:
            if s['pending_publish_id'] in by_episode:
                by_episode[s['pending_publish_id']].append(s)
            else:
                by_episode[s['pending_publish_id']] = [s]
        # process each list
        for ep_id, subscriptions in by_episode.items():
            cursor.execute("SELECT * FROM episodes WHERE id = %s", [ep_id])
            episode = cursor.fetchone()
            publish_episode(cursor=cursor, episode=episode, subscriptions=subscriptions)
