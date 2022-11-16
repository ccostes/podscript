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
from db import connect
from storage import get_episode, get_pending_subscriptions, update_subscription, set_episode_archive
from email.generate import generate

def process_sub(connection, sub):
    logging.info(f"Processing pending subscription {sub['id']}, pending_publish_id: {sub['pending_publish_id']}")
    ep = get_episode(connection=connection, id=sub['pending_publish_id'])
    if ep['archive'] == 1:
        set_episode_archive(connection=connection, id=ep['id'], archive=0)
    # Check if episode processing is complete
    if ep['state'] == 4:
        print(f"Episode {ep['id']} ready to publish!")
        # TODO: actually publish
        generate(episode=ep, transcript_file='transcript.json')
        sub['last_published'] = sub['pending_publish']
        sub['last_published_id'] = sub['pending_publish_id']
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