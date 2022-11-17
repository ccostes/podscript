"""
Process subscriptions pending publish
for each sub where `pending_publish != null`
- ep = episode where `podcast_id` matches sub and `publish` = `pending_publish`
- set `ep.archive = 0`
- if `state` = 3 (processed, transcript available)
    - publish episode to subscription email
    - set last_published to pending_published
    - set `pending_publish = null`
"""
import logging
from supabase import supa_connect, handle_new_user
from db import connect, get_podcast, get_user
from storage import get_episode, get_episode_path, get_pending_subscriptions, update_subscription, set_episode_archive
from email.generate import generate
from mail import publish
from dotenv import dotenv_values
env = dotenv_values('.env.local')

def publish_sub(connection, sub, ep):
    user = get_user(connection, sub['user_id'])
    pod = get_podcast(connection, sub['podcast_id'])
    episode_path = Path(env['STORAGE_PATH']) / get_episode_path(connection, ep['id'])
    email_html = generate(episode=ep, transcript_file=episode_path / 'transcript.json')
    to_email = user['email']
    publish(
        to_email=to_email, 
        subject=pod['title'] + ": " + ep['title'], 
        body=email_html, 
        art_url=pod['art_url']
    )

def process_sub(connection, sub):
    logging.info(f"Processing pending subscription {sub['id']}, pending_publish_id: {sub['pending_publish_id']}")
    ep = get_episode(connection=connection, id=sub['pending_publish_id'])
    if ep['archive'] == 1:
        set_episode_archive(connection=connection, id=ep['id'], archive=0)
    # Check if episode processing is complete
    if ep['state'] == 4:
        print(f"Episode {ep['id']} ready to publish!")
        publish_sub(connection, sub, ep)
        # update subscription published/pending
        sub['last_published'] = sub['pending_publish']
        sub['last_published_id'] = sub['pending_publish_id']
        sub['pending_publish'] = None
        sub['pending_publish_id'] = None
        update_subscription(connection=connection, sub=sub)

def main():
    with connect() as connection:
        subs = get_pending_subscriptions(connection=connection)
        for sub in subs:
            process_sub(connection=connection, sub=sub)

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()