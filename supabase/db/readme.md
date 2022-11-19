# Supabase DB
Schema:
## Tokens
Table to map identifier tokens to user IDs
* id - foreign key to the users ID column
* updated_at
* token

## Auth.Users
Schema defined by supabase.

### Triggers
#### User verified
On table update when email_confirmed is set, trigger the user_verified() function.

## Subscriptions
* id INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
* created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
* podcast_id INTEGER NOT NULL,
* user_id INTEGER NOT NULL,
* last_published DATETIME DEFAULT NULL,
* last_published_guid INTEGER DEFAULT NULL,
* last_published_id INTEGER DEFAULT NULL,
* pending_publish_id INTEGER DEFAULT NULL

## Podcasts
* id INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
* title TEXT,
* feed_url VARCHAR(512) UNIQUE NOT NULL,
* author TEXT,
* link TEXT NOT NULL,
* description TEXT,
* image_url TEXT,
* http_modified TEXT,
* http_etag TEXT,
* file_prefix - prefix used to identify files for this podcast (followed by episode prefix)
* apple_id INTEGER,

### Triggers
#### New Podcast
On insert, call webhook to get podcast feed data

## Episodes
* id INTEGER PRIMARY KEY NOT NULL AUTO_INCREMENT,
* podcast_id TEXT NOT NULL,
* title TEXT,
* description TEXT,
* episode_url TEXT,
* published DATETIME NOT NULL,
* guid TEXT NOT NULL,
* link TEXT NOT NULL,
* mime_type VARCHAR(64) NOT NULL DEFAULT 'application/octet-stream',
* filename TEXT NOT NULL,
* total_time INTEGER NOT NULL DEFAULT 0,
* description_html TEXT,
* image_url TEXT,

### Triggers
#### New Episode
On insert, call `new_episode()` to update relevant subscriptions

#### Episode filename updated
Episode filename is updated when the transcription files are available for the episode.

Can notify on a `files_ready` channel to trigger publishing

# Functions
Database triggers are used to implement flows for account creation, verification, and unsubscribe

## Account Verification - `user_verified()`
Account verification occurs when the user clicks the link in the verification email. When that occurs we need to:
* Query podcasts table for feed url
  * if present, save podcast ID for subscription record
  * else, insert new podcast row with feed URL and apple ID - rest will be populated later
* Create a subscription for the user with user_id and podcast_id

## New-podcast - `new_podcast()`
When a new podcast is added we need to fetch the feed data. Would be nice to do this with an edge-function, but it doesn't look like there are any js feed parsers for podcasts like what I already have working in python, so I'm just going to stick with that and use the postgres notify method I got working previously.

For now that will just run 'on-prem', but could easily be moved to the cloud later.

This function just emits a notify for inserts to the podcasts table.

## New-episode - `new_episode()`
When a new episode is inserted, need to updated all subscriptions for that podcast
* Query subscriptions filtering on podcast_id, for each:
  * if pending_publish_id = NULL
    * set pending_publish and pending_publish_id to new episode