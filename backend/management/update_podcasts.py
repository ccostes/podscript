"""
Poll podcasts for new episodes.
"""
import json, logging
import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
from util.supabase import supa_connect
from feeds import update_feed

def main():
    conn = supa_connect()
    cursor = conn.cursor()
    
    logging.info("Updating podcast feeds...")
    cursor.execute("SELECT * FROM podcasts")
    pods = cursor.fetchall()
    for pod in pods:
        update_feed(cursor=cursor, podcast=pod)

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
