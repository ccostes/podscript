import re, unicodedata, datetime, time, logging
import mariadb
import feedparser
from db import connect, insert_user, insert_subscription, update_subscription, get_subscriptions, get_user_by_uuid
"""
Provide an interface to the underlying SQL storage layer for podcasts, episodes, 
users, and subscriptions.
"""
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

## if key already exists (url) updates last_modified and etag
def insert_podcast(connection, apple_id, data):
    # first fill any missing text fields with empty strings
    url = data.href
    title = "" if data.feed.title is None else data.feed.title
    author = "" if data.feed.author is None else data.feed.author
    link = "" if data.feed.link is None else data.feed.link
    description = "" if data.feed.description is None else data.feed.description
    artwork_url = "" if data.feed.image.href is None else data.feed.image.href
    http_last_modified = "" if data.modified is None else data.modified
    http_etag = "" if data.etag is None else data.etag
    download_folder = to_directory_name(author + " " + title)
    insert_query = """
    INSERT INTO podcasts
        (apple_id,
        url, 
        title, 
        author, 
        link, 
        description, 
        artwork_url, 
        http_last_modified, 
        http_etag, 
        download_folder)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    row = None
    with connection.cursor() as cursor:
        try:
            cursor.execute(insert_query, [
                apple_id, 
                url, 
                title, 
                author, 
                link, 
                description, 
                artwork_url, 
                http_last_modified, 
                http_etag, 
                download_folder
            ])
            connection.commit()
            row = cursor.lastrowid
        except mariadb.connector.errors.IntegrityError:
            # record already exists - update
            logging.info(f"upsert_podcast podcast already exists - updating url: {url}")
            update_query = "UPDATE podcasts SET http_last_modified = %s, http_etag = %s WHERE url = %s"
            cursor.execute(update_query, (http_last_modified, http_etag, url))
            cursor.execute("SELECT id FROM podcasts WHERE url = %s", [url])
            r = cursor.fetchone()
            row = None if r is None else r[0]
            connection.commit()
    return row

def insert_episode(cursor, podcast_id, archive, ep):
    guid = ep.id
    title = "" if ep.title is None else ep.title
    description = "" if ep.summary is None else ep.summary
    description_html = ""
    for c in ep.content:
        if c.type == "text/html":
            description_html = c.value
        if c.type == "text/plain":
            description = c.value
    published = datetime.datetime.fromtimestamp(time.mktime(ep.published_parsed)).strftime('%Y-%m-%d %H:%M:%S')
    link = "" if ep.link is None else ep.link
    file_size = 0
    url = ""
    mime_type = ""
    for l in ep.links:
        if l.rel == "enclosure":
            file_size = l.length
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
            ss = parts
        else:
            logging.error(f"Unrecognized itunes_duration: '{ep.itunes_duration}' podcast ID: {podcast_id} episode guid: {guid}")
        total_time = int(hh) * 3600 + int(mm) * 60 + int(ss)
    download_filename = ""

    insert_query = """
    INSERT INTO episodes (
        podcast_id,
        guid,
        title,
        description,
        description_html,
        published,
        link,
        file_size,
        url,
        mime_type,
        download_filename,
        total_time,
        archive
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (podcast_id,guid,title,description,description_html,published,link,file_size,url,mime_type,download_filename,total_time,archive))

def insert_new_episodes(connection, data, podcast_id, published_after=None):
    episodes = data.entries
    with connection.cursor() as cursor:
        # Check to see if there are any existing episodes - if so, insert new as archive=0, 1 otherwise
        cursor.execute("SELECT COUNT(*) FROM podcasts WHERE id = %s", [podcast_id])
        existing = cursor.fetchone()[0]
        archive = 0
        if existing == 0:
            logging.info("New podcast, inserting {len(episodes)} episodes as archived")
        else:
            logging.info(f"Inserting {len(episodes)} new episodes for existing podcast!")

        for idx, ep in enumerate(episodes):
            # Make sure episode is published more recently than published_after
            published = datetime.datetime.fromtimestamp(time.mktime(ep.published_parsed))
            if published_after is not None and published < published_after:
                continue
            insert_episode(cursor=cursor, podcast_id=podcast_id, archive=archive, ep=ep)
        connection.commit()

def import_feed(connection, apple_id, url):
    # fetch a new feed and add it to the database
    logging.info(f"Importing feed - Apple ID: {apple_id} URL: {url}")
    # first check to see if we already have it
    existing = get_podcast_by_url(connection=connection, url=url)
    if existing is not None:
        logging.info(f"Already have podcast record for feed url, skipping import")
        return
    d = feedparser.parse(url)
    podcast_id = insert_podcast(connection=connection, apple_id=apple_id, data=d)
    insert_new_episodes(connection=connection, data=d, podcast_id=podcast_id)

def get_pending_subscriptions(connection):
    with connection.cursor(buffered = True, dictionary=True) as cursor:
        cursor.execute("SELECT * FROM subscriptions WHERE pending_publish != NULL")
        return cursor.fetchall()

def import_user_sub(connection, user_id, token, email, podcast_id, feed_url):
    podcast = get_podcast_by_url(connection=connection, url=feed_url)
    if podcast is None:
        import_feed(connection=connection, apple_id=podcast_id, url=feed_url)
    podcast = get_podcast_by_url(connection=connection, url=feed_url)
    user = get_user_by_uuid(connection=connection, uuid=user_id)
    if user is None:
        insert_user(connection=connection, user_id=user_id, token=token, email=email)
    user = get_user_by_uuid(connection=connection, uuid=user_id)
    
    insert_subscription(connection=connection, user_id=user['id'], podcast_id=podcast['id'])

def get_next_episode(connection, podcast_id, datetime):
    query = "SELECT * FROM episodes WHERE podcast_id = %s AND published > %s ORDER BY published ASC LIMIT 1"
    cursor = connection.cursor(buffered = True, dictionary=True)
    cursor.execute(query, [podcast_id, datetime])
    t = cursor.fetchone()
    return t

# Returns a datetime of the most recent episode for the podcast with the given url, or None
def get_most_recent_episode(connection, podcast_id):
    query = """
    SELECT * FROM episodes WHERE podcast_id = %s ORDER BY published DESC LIMIT 1
    """
    cursor = connection.cursor(buffered = True, dictionary=True)
    cursor.execute(query, [podcast_id])
    t = cursor.fetchone()
    return t

def get_podcast_by_url(connection, url):
    with connection.cursor(buffered=True, dictionary=True) as cursor:
        cursor.execute("SELECT * FROM podcasts where url = %s", [url])
        result = cursor.fetchall()
        if len(result) == 1:
            return result[0]
        else:
            return None

def get_podcasts(connection):
    with connection.cursor(buffered=True, dictionary=True) as cursor:
        cursor.execute("SELECT * FROM podcasts")
        result = cursor.fetchall()
    return result

def get_episodes_with_state(connection, state):
    with connection.cursor(buffered=True, dictionary=True) as cursor:
        cursor.execute("SELECT * FROM episodes WHERE archive = 0 AND state = %s", [state])
        result = cursor.fetchall()
    return result

def get_episode(connection, id):
    with connection.cursor(buffered=True, dictionary=True) as cursor:
        cursor.execute("SELECT * FROM episodes WHERE id = %s", [id])
        result = cursor.fetchall()
    return result

def get_episode_path(connection, id):
    with connection.cursor(buffered=True, dictionary=True) as cursor:
        cursor.execute("""SELECT episodes.id, published, download_folder FROM episodes 
        JOIN podcasts ON podcasts.id = episodes.podcast_id
        WHERE episodes.id = %s""", [id])
        res = cursor.fetchone()
        return res['download_folder'] + "/" + res['published'].strftime("%Y-%m-%d_%H-%M-%S") + "_" + res['id']


def set_episode_archive(connection, id, archive):
    with connection.cursor(buffered=True, dictionary=True) as cursor:
        cursor.execute("UPDATE episodes SET archive = %s WHERE id = %s", [archive, id])
        result = cursor.fetchall()
    return result

def update_episode_state(connection, id, new_state):
    with connection.cursor(buffered=True, dictionary=True) as cursor:
        cursor.execute("UPDATE episodes SET state = %s WHERE id = %s", [new_state, id])
        connection.commit()
        cursor.execute("SELECT * FROM episodes WHERE id = %s", [id])
        result = cursor.fetchall()
    return result

def update_feed(connection, id, url, etag=None, modified=None):
    # Attempt to fetch feed
    d = feedparser.parse(url, etag=etag, modified=modified)
    # Check to see if we got anything (could be no updates)
    if d.status == 304:
        # We're all up to date!
        return False
    if d.status == 410:
        # Feed has been permanently deleted
        # TODO: do something about that
        return False
    if d.status == 301:
        # Permanent redirect
        # TODO: update our feed url to d.href
        logging.info("Feed permanently moved!")
    # update feed
    # podcast_id = insert_podcast(connection=connection, data=d)
    logging.info(f"Got feed update for podcast ID: {id}")

    # find new feed entries
    our_latest = get_most_recent_episode(connection=connection, podcast_id=id)
    logging.info(f"Inserting episodes more recent than {our_latest['published']}")
    insert_new_episodes(connection=connection, data=d, published_after=our_latest['published'], podcast_id=id)

def update_feeds(connection):
    with connection.cursor(buffered = True, dictionary=True) as cursor:
        cursor.execute("select id, url, http_etag,http_last_modified from podcasts")
        for pod in cursor:
            logging.info(f"Updating podcast ID {pod['id']}")
            update_feed(connection=connection, 
                id=pod['id'], 
                url=pod['url'], 
                etag=pod['http_etag'], 
                modified=pod['http_last_modified'])

# Update feeds
def main():
    connection = connect()
    # import_feed(connection, "feed.atom")
    # import_feed(connection, "https://feeds.simplecast.com/54nAGcIl")
    update_feeds(connection=connection)
    
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()