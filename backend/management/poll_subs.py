
import sys, time, logging
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
from util.supabase import supa_connect
from publishing import poll_pending_subs

def main():
    conn = supa_connect()
    cursor = conn.cursor()
    logging.info("Polling subscriptions...")
    while True:
        poll_pending_subs(cursor=cursor)
        time.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
