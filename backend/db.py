import re, unicodedata, datetime, time, logging
import mariadb
from mariadb import connect as mysql_connect, Error
from dotenv import dotenv_values
env = dotenv_values('.env.local')
"""
DB interface layer
"""
def connect():
    return mysql_connect(
        host=env['BACKEND_DB_HOST'],
        user=env['BACKEND_DB_USER'],
        password=env['BACKEND_DB_PASSWORD'],
        database=env['BACKEND_DB_DATABASE'],
    )

create_subs_table_query = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    podcast_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    last_published DATETIME DEFAULT NULL,
    last_published_id INTEGER DEFAULT NULL,
    pending_publish DATETIME DEFAULT NULL,
    pending_publish_id INTEGER DEFAULT NULL
)"""
create_users_table_query = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
    uuid VARCHAR(255) UNIQUE NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(255)
)"""
create_podcasts_table_query = """
CREATE TABLE IF NOT EXISTS podcasts (
    id INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
    apple_id INTEGER,
    url VARCHAR(512) UNIQUE NOT NULL,
    title TEXT,
    author TEXT,
    link TEXT NOT NULL,
    description TEXT,
    artwork_url TEXT,
    http_last_modified TEXT,
    http_etag TEXT,
    download_folder TEXT NOT NULL,
    subscriber_count INTEGER NOT NULL DEFAULT 0
)"""
create_episodes_table_query = """
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
    podcast_id TEXT NOT NULL,
    title TEXT,
    description TEXT,
    url TEXT,
    published DATETIME NOT NULL,
    guid TEXT NOT NULL,
    link TEXT NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    mime_type VARCHAR(64) NOT NULL DEFAULT 'application/octet-stream',
    state INTEGER NOT NULL DEFAULT 0,
    is_new INTEGER NOT NULL DEFAULT 0,
    archive INTEGER NOT NULL DEFAULT 0,
    download_filename TEXT NOT NULL,
    total_time INTEGER NOT NULL DEFAULT 0,
    description_html TEXT,
    episode_art_url TEXT,
    chapters TEXT
)"""
def create_tables(connection):
    cursor = connection.cursor()
    cursor.execute(create_podcasts_table_query)
    cursor.execute(create_episodes_table_query)
    cursor.execute(create_users_table_query)
    cursor.execute(create_subs_table_query)
    connection.commit()

def insert_user(connection, user_id, token, email):
    logging.info(f"Inserting user - ID: {user_id}")
    insert_query = "INSERT IGNORE INTO users (uuid, token, email) VALUES (%s, %s, %s)"
    with connection.cursor() as cursor:
        cursor.execute(insert_query, [user_id, token, email])
    connection.commit()

def get_user(connection, id):
    with connection.cursor(buffered=True, dictionary=True) as cursor:
        cursor.execute("SELECT * FROM users where id = %s", [id])
        return cursor.fetchone()

def get_user_by_uuid(connection, uuid):
    with connection.cursor(buffered=True, dictionary=True) as cursor:
        cursor.execute("SELECT * FROM users where uuid = %s", [uuid])
        result = cursor.fetchall()
        if len(result) == 1:
            return result[0]
        else:
            return None

def get_subscriptions(connection):
    with connection.cursor(buffered = True, dictionary=True) as cursor:
        cursor.execute("SELECT * FROM subscriptions")
        return cursor.fetchall()

def insert_subscription(connection, user_id, podcast_id):
    logging.info(f"Inserting subscription to podcast {podcast_id} for user {user_id}")
    insert_query = """
        INSERT INTO subscriptions (user_id, podcast_id) VALUES (%s, %s)
    """
    with connection.cursor(buffered = True, dictionary=True) as cursor:
        cursor.execute("SELECT * FROM subscriptions WHERE user_id = %s AND podcast_id = %s", [user_id, podcast_id])
        res = cursor.fetchall()
        if res == []:
            cursor.execute(insert_query, [user_id, podcast_id])
        else:
            logging.info("Subscription for user and podcast already exists")
    connection.commit()

def update_subscription(connection, sub):
    logging.info(f"Updating subscription: {sub}")
    with connection.cursor(buffered = True, dictionary=True) as cursor:
        cursor.execute("""UPDATE subscriptions SET 
            podcast_id = %s, 
            last_published = %s, 
            last_published_id = %s, 
            pending_publish = %s, 
            pending_publish_id = %s""", 
            [
                sub.get('podcast_id'), 
                sub.get('last_published'), 
                sub.get('last_published_id'), 
                sub.get('pending_publish'), 
                sub.get('pending_publish_id')])
    connection.commit()

def get_podcast(connection, id):
    with connection.cursor(buffered=True, dictionary=True) as cursor:
        cursor.execute("SELECT * FROM podcasts where id = %s", [id])
        return cursor.fetchone()

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    conn = connect()
    create_tables(connection=conn)