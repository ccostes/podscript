# Podscript

Directories:
* **app** - Supabase frontend 
* **backend** - Scripts for running the backend feed and subscription processing

# Data Schema
Data is separated between supabase and the local DB. Supabase contains all user and subscription records, and the local database contains podcast and episode data. 

## Supabase Schemas
### Subscriptions
* id
* created_at
* user_id - supabase ID of the user who owns the subscription
* podcast_apple_id - apple ID for the podcast; not guaranteed to be present if we support custom feed URLs
* podcast_url - the feed URL of the podcast; this is our primary identifier of podcasts
* last_published - datetime when the subscription was last published
* last_published_id - our episode ID of the last episode that was published for the subscription
* last_published_guid - guid of the last episode published, mostly for recovery purposes

# Backend Functions
The backend is responsible for podcasts and subscription publishing: maintaining a catalog of podcast feeds for all subscriptions, periodically updating those feeds to store new episode records, processing new episodes, and publishing subscriptions when there are new episodes available. 

When a new episode is available it needs to start the transcription job pipeline and store the resulting data (transcript json and txt - don't need audio data).

When subscriptions have new episodes available, emails need to be published.

## Subscriptions
Subscriptions are periodically processed. 

First we check for new subscriptions, filtering for last_published and pending_publish both null:
 - check if we have the podcast feed url in our db, if not, add it
 - set pending_publish to the most recent episode

Next we check for subscriptions that have a publish pending:
- check if the pending episode processing is complete
- if so, publish!

## Podacsts
Podcasts are periodically polled to check for new episodes. If a new episode is added:
- set pending_publish to the new episode for all subscriptions for this podcast URL with pending_publish = null

## Episode Processing
Lastly, need to manage the processing pipeline for episodes. This job is on the processing machine (windows laptop) and periodically polls, querying for episodes where archive=0 and state != 4. 

Episodes are processed serially, and prioritized by oldest publish date and highest processing state. A single directory is used to hold intermediate files during processing and cleaned out between runs.

Switch on state:
  - 0: ready to process 
    - download audio file into processing dir and create jobfile to kick off stage 1 of pipeline
  - 1: Stage 1 (padding and diarization) complete, ready for transcription
    - update job file and rename to kick of transcription
  - 2: transcription complete, final transcript and email files ready
    - copy artifacts to pi storage and clean up processing folder
