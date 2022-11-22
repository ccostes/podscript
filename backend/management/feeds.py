"""
Keep feeds updated! Listens to feed DB inserts to do initial fetch for new feeds.
"""
import logging, datetime, time, re, unicodedata
from urllib.parse import urlparse
import feedparser

def to_directory_name(value, allow_unicode=False):
    """
    From Django slugify:
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")

def update_podcast(cursor, feed_url, data):
    # performs a sparse update of the existing record (so will not clear any fields)
    update = {}
    update['feed_url'] = data.href
    update['title'] = data.feed.title
    update['author'] = data.feed.author
    update['link'] = data.feed.get('link')
    update['description'] = data.feed.description
    update['image_url'] = data.feed.image.href
    update['http_modified'] = data.get('modified')
    update['http_etag'] = data.get('etag')
    
    # get existing record
    cursor.execute("SELECT * FROM podcasts WHERE feed_url = %s", [feed_url])
    existing = cursor.fetchone()
    if existing is None:
        logging.error(f"Error: no existing podcast record for feed: {feed_url}")

    # File prefix is the apple ID if it exists, otherwise the feed url
    if 'apple_id' in existing and existing['apple_id'] is not None:
        update['file_prefix'] = existing['apple_id']
    else:
        uri = urlparse(feed_url)
        update['file_prefix'] = to_directory_name(uri.netloc + uri.path)

    # merge update onto existing, first remove None values from existing and update
    existing_filtered = {k: v for k,v in dict(existing).items() if v is not None}
    update_filtered = {k: v for k,v in update.items() if v is not None}
    # now merge - update keys will override existing
    merged = existing_filtered | update_filtered 

    insert_query = """
    UPDATE podcasts SET
        feed_url=%s,
        title=%s, 
        author=%s, 
        link=%s, 
        description=%s, 
        image_url=%s, 
        http_modified=%s, 
        http_etag=%s, 
        file_prefix=%s
    WHERE id = %s
    """
    cursor.execute(insert_query, [
        merged.get('feed_url'),
        merged.get('title'),
        merged.get('author'),
        merged.get('link'),
        merged.get('description'),
        merged.get('image_url'),
        merged.get('http_modified'),
        merged.get('http_etag'),
        merged.get('file_prefix'),
        merged.get('id'),
    ])
    cursor.execute("SELECT * FROM podcasts WHERE id = %s", [merged['id']])
    return cursor.fetchone()

def insert_episode(cursor, podcast_id, ep):
    description = None
    if 'description' in ep:
        description = ep.get('description')
    if 'summary' in ep:
        description = ep.get('summary')
    description_html = None
    if 'content' in ep:
        for c in ep.get('content'):
            if c.type == "text/html":
                description_html = c.value
            if c.type == "text/plain":
                description = c.value
    if 'summary_detail' in ep:
        if 'type' in ep['summary_detail']:
            if ep['summary_detail']['type'] == "text/html":
                description_html = ep['summary_detail']['value']
            if ep['summary_detail']['type'] == "text/plain":
                description = ep['summary_detail']['value']

    published = datetime.datetime.fromtimestamp(time.mktime(ep.published_parsed)).strftime('%Y-%m-%d %H:%M:%S')
    url = ""
    mime_type = ""
    for l in ep.links:
        if l.rel == "enclosure":
            # file_size = l.length
            url = l.href
            mime_type = l.type
    if 'itunes_duration' not in ep:
        total_time = 0
    else:
        hh, mm, ss = 0,0,0
        parts = ep.itunes_duration.split(':')
        if len(parts) == 3:
            hh, mm, ss = parts
        elif len(parts) == 2:
            mm, ss = parts
        elif len(parts) == 1:
            ss = parts[0]
        else:
            logging.error(f"Unrecognized itunes_duration: '{ep.itunes_duration}' podcast ID: {podcast_id} episode guid: {ep.id}")
        total_time = int(hh) * 3600 + int(mm) * 60 + int(ss)
    insert_query = """
    INSERT INTO episodes (
        podcast_id,
        title,
        description,
        episode_url,
        published,
        guid,
        link,
        mime_type,
        total_time,
        description_html,
        image_url
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, [
        podcast_id,
        ep.title,
        description,
        url,
        published,
        ep.get('id'),
        ep.get('link'),
        mime_type,
        total_time,
        description_html,
        ep.image.href if ep.get('image') else None
    ])

def insert_new_episodes(cursor, data, podcast_id):
    # First check to see what the most recent episode we already have is
    cursor.execute("SELECT * FROM episodes WHERE podcast_id = %s ORDER BY published DESC LIMIT 1", [podcast_id])
    most_recent = cursor.fetchone()
    if most_recent is None:
        # initial import - only want to add the most recent episode (should be the first entry)
        logging.info(f"Initial import for podcast {podcast_id}, inserting first episode only")
        insert_episode(cursor=cursor, podcast_id=podcast_id, ep=data.entries[0])
        return 1
    
    published_after = most_recent['published'].replace(tzinfo=None)
    count = 0
    for ep in data.entries:
        # Make sure episode is published more recently than published_after
        published = datetime.datetime.fromtimestamp(time.mktime(ep.published_parsed)).replace(tzinfo=None)
        if published > published_after:
            count += 1
            insert_episode(cursor=cursor, podcast_id=podcast_id, ep=ep)
    logging.info(f"Inserted {count} new episodes for podcast {podcast_id}!")
    return count

def update_feed(cursor, podcast):
    # Attempt to fetch feed
    d = feedparser.parse(
        podcast['feed_url'],
        etag=podcast.get('http_etag'),
        modified=podcast.get('http_modified'),
    )
    # Check to see if we got anything (could be no updates)
    if d.status == 304:
        # We're all up to date!
        return False
    if d.status == 410:
        # Feed has been permanently deleted
        logging.info(f"Podcast permanently deleted! ID {podcast['id']} feed_url: {podcast['feed_url']}")
        # TODO: do something about that
        return False
    if d.status == 301:
        # Permanent redirect
        logging.info(f"Feed permanently moved! ID {podcast['id']} feed_url: {podcast['feed_url']}")
        # TODO: update our feed url to d.href
    # Got feed update! Update podcasts table
    logging.info(f"Got feed update for podcast ID: {podcast['id']}")
    updated = update_podcast(
        cursor=cursor,
        feed_url=podcast['feed_url'],
        data=d
    )
    # Import new episodes
    count = insert_new_episodes(
        cursor=cursor,
        podcast_id=updated['id'],
        data=d
    )
    if count > 0:
        # Update pending_publish_id for all subscriptions
        logging.info("Inserted new episodes, updating subscriptions pending_publish_id")
        cursor.execute("""
        UPDATE subscriptions as sub SET pending_publish_id = 
            CASE WHEN sub.last_published IS NULL THEN 
                (SELECT id FROM episodes 
                    WHERE podcast_id = sub.podcast_id 
                    ORDER BY published DESC LIMIT 1)
            ELSE
                (SELECT id from episodes 
                    where podcast_id = sub.podcast_id 
                    and published > sub.last_published 
                    order by published ASC LIMIT 1) 
            END
            WHERE pending_publish_id IS NULL
        """)