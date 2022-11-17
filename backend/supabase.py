import logging
from db import connect, get_user_by_uuid
from storage import import_user_sub
import psycopg2
import psycopg2.extras
from dotenv import dotenv_values
env = dotenv_values('.env.local')

def supa_connect():
    conn = psycopg2.connect(
        database=env['SUPABASE_DB_USER'], 
        host=env['SUPABASE_DB_HOST'], 
        port=5432, 
        user=env['SUPABASE_DB_USER'], 
        password=env['SUPABASE_DB_PASSWORD'],
        cursor_factory=psycopg2.extras.DictCursor,
    )
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn

"""
Sync users and subscriptions from supabase to local db
"""

def handle_new_user(connection, data):
    podcast = data['raw_user_meta_data']['user_metadata']['podcast']
    import_user_sub(
        connection=connection, 
        user_id=data['id'],
        token=data['token'],
        email=data['email'],
        podcast_id=podcast['apple_id'],
        feed_url=podcast['feed_url'],
    )

def sync_users(su_conn):
    su_cursor = su_conn.cursor()
    su_cursor.execute("""select auth.users.id, auth.users.email, auth.users.raw_user_meta_data, 
    public.tokens.token 
    from auth.users 
    join public.tokens on public.tokens.id = auth.users.id """)
    users = su_cursor.fetchall()
    with connect() as my_connection:
        my_cur = my_connection.cursor(buffered=True, dictionary=True)
        for u in users:
            if get_user_by_uuid(connection=my_connection, uuid=u['id']) is None:
                logging.info(f"Found missing user: {u}")
                handle_new_user(connection=my_connection, data=u)

def main():
    su_conn = supa_connect()
    sync_users(su_conn)

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()