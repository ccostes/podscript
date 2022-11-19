# Podscript

Directories:
* **app** - Supabase frontend 
* **supabase** - supabase backend stuff - DB schema, triggers, functions, and scripts

# Data Schema
See `./supabase/db/readme.md`

# Data Flows

## Account Verification
Account verification triggers the creation of:
* account token
* podcast (if doesn't exist)
* subscription

The flow is as follows:
Verification link clicked -> 
`email_confirmed_at` on auth.users updated -> triggers `user_verified()` function
  - creates token
  - creates podcast if not exists -> triggers `new_podcast()`
    - sends notify on `new_podcast` channel
  - creates subscription

## New Podcast
When a new podcast is inserted into the `podcasts` table it sends a notify on `new_podcast`

The `./supabase/db/feeds.py` script listens to this, starting the feed update process which will populated the podcast record with all the data and insert the most recent episode.

## New Episode
When a new episode is inserted into the `episodes` table it triggers `new_episode()` which updates all subscriptions for that podcast with `pending_publish_id` = NULL, setting `pending_publish_id` to the newly inserted episode ID.

It also notifies on `new_episode` which kicks off transcription generation.

## New Transcript
When a new transcript is complete, the email html is uploaded to R2 and the object ID is set on the episode `filename` column. This update triggers the `new_transcript()` function which notifies on `new_transcript`. The mailer script listens to `new_transcript` and processes subscription publishing for the new transcript.
