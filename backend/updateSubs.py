"""
Update subscriptions last/pending publish records
for each sub:
- if `last_published` is `null`, new subscription
    - ep = most recent episode
    - set `pending_publish` to ep.published
- else if `pending_publish` is null and `last_published` is older than the most recent episode
    - ep = next episode published after `last_published`
    - set `pending_publish` to ep.published
"""
import logging
from db import connect
from storage import get_next_episode, get_most_recent_episode, get_subscriptions, update_subscription

def update_sub(connection, sub):
    if sub.get('last_published') is not None and sub.get('pending_publish') is None:
        # Set `pending_publish` to next-most recent episode
        next = get_next_episode(
            connection=connection, 
            podcast_id=sub['podcast_id'], 
            datetime=sub['last_published']
        )
        sub['pending_publish'] = next['published']
        sub['pending_publish_id'] = next['id']
        update_subscription(connection=connection, sub=sub)
    else:
        # new subscription - set `pending_publish` to most recent episode
        next = get_most_recent_episode(connection=connection, podcast_id=sub['podcast_id'])
        sub['pending_publish'] = next['published']
        sub['pending_publish_id'] = next['id']
        update_subscription(connection=connection, sub=sub)

def main():
    with connect() as connection:
        subs = get_subscriptions(connection=connection)
        for sub in subs:
            update_sub(connection=connection, sub=sub)

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()