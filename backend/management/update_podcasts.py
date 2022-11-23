"""
Poll podcasts for new episodes.
"""
import json, logging, time
import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
from util.supabase import supa_connect
from feeds import update_feed

def update_all(cursor):
    cursor.execute("SELECT * FROM podcasts")
    pods = cursor.fetchall()
    for pod in pods:
        update_feed(cursor=cursor, podcast=pod)

def main():
    conn = supa_connect()
    cursor = conn.cursor()
    # Get count of podcasts
    cursor.execute("SELECT COUNT(*) FROM podcasts")
    pod_count = cursor.fetchone()
    logging.info(f"Starting podcast feed update loop, podcast count: {pod_count}")
    # every 10 seconds check for new podcasts and update any new ones
    # every 10 minutes (60 iterations) update all feeds
    iter = 0
    while True:
        # get podcast count
        cursor.execute("SELECT COUNT(*) FROM podcasts")
        count = cursor.fetchone()
        if count > pod_count:
            logging.info(f"New podcast added! prev count: {pod_count} new count: {count}")
            pod_count = count
            update_all(cursor=cursor)
            iter = 0

        if iter >= 60:
            update_all(cursor=cursor)
            iter = 0

        iter += 1
        time.sleep(10)
    
if __name__ == "__main__":
    logging.basicConfig(
        filename='update_podcasts.log',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
