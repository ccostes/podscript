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
