from feeds import supa_connect, update_feed

conn = supa_connect()
cursor = conn.cursor()
update_feed(cursor=cursor, podcast={'id': 12, 'feed_url': 'https://audioboom.com/channels/4964339.rss'})