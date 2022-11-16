# 11/15
- deciding on file storage schema
  - within podcasts folder `/storage/<podcast download directory>/<publish date>_<guid>`
    - want raw transcript json (array of objects w/ speaker and text, maybe other stuff)
    - finished html and plaintext transcripts ready to email
- Thinking about the email experience
  - Sender is Podscript, so don't think I need to worry about brand misrepresentation issues
    - probably still want to make it clear in the header that it's from Podscript and not whatever brand the podcast is by
    - was thinking about branding of some sort, but maybe just a `Generated for you with 💛 by Podscript`
  - Subject `<Podcast Title> - <Truncated Episode title ...>`
    - could also have the subject just be podcast title and use preview text for episode title
- Awesome progress today, focussing on emails
  - got nice looking, minimal, template created with mjml
  - putting the podcast artwork and episode description html at the top, followed by transcript
  - looks freaking awesome
  - need to update ingestion pipeline to save apple artwork URL
- next step is really to wire everything together
  - move this backend stuff to the pi
  - get files going back and forth between the pi and windows laptop
    - probably want to have the win machine read directly from the db on the pi and ssh finished transcript files back
  - create cronjobs/make everything run persistently

# 11/14
- Full signup-to-backend flow working!!
  - sign up and select podcast, when email confirmation link clicked:
    - token generated on supabase
    - notification sent to backend
    - backend imports podcast if not present, creates user, creates subscription
- considering how to manage episode state, when to decide what should be archived or not
  - think it should be separate logic from updating episodes for feed
- publisher job
  - update subscriptions - for each sub:
    - if `last_published` is `null`, new subscription
      - ep = most recent episode
      - set `pending_publish` to ep.published
    - else if `last_published` is older than the most recent episode
      - ep = next episode published after `last_published`
      - set `pending_publish` to ep.published
  - process pending subs - for each sub where `pending_publish != null`
    - ep = episode where `podcast_id` matches sub and `publish` = `pending_publish`
    - set `ep.archive = 0`
    - if `state` = 3 (processed, transcript available)
      - publish episode to subscription email
      - set `pending_publish = null`
- processing job calls `episodes_by_state` api endpoint
  - API will only return episodes where `archive == 0`
- Going to create a new pipeline stage for transforming a transcription into the final email transcript

# 11/13
- Got email magic link signup working
  - though found a bug with custom SMTP settings
- Created `tokens` table to store a custom token (changeable) for each user
  - token will be used as query param to identify user in email action links such as unsubscribe or change subscription
  - have a trigger on the auth.users table to create token when user inserted
    - this is not related to a user verifying their email
- Created an update trigger on auth.users for the email_confirmed_at column to detect verifications
  - notifies on `user_verified` channel
- did a whole bunch of frontend work getting the podcast search UI looking the way I want and getting it wired up to apple's podcast search
  - spent probably too much time figuring out tailwind css and looking at overcast's search to get a fancy search bar with dynamic results that show up below it
  - but it came together and looks legit, and 'just worked' when I pointed it to apple's API instead of a static results list!
- Figured out how to use postgres triggers and notify to create token and notify backend when user verifies email
  - sends the whole user record with the token, which includes `raw_user_meta_data` which is the apple podcast object that the user selected during sign-up!
- Now on the backend I can maintain a list of users and their subscriptions
  - when I get a user verified notification
    - potentially ingest new podcast if we haven't seen it before
    - create new subscription for the user to the podcast
- Might change things to only record the podcast ID in the metadata - don't really need the whole record
  - not that much extra data, so not a big deal right now

# 11/10
- thinking about initial user flow
  - 'default' approach is creating account / sign-in with oauth, then subscribe
  - want a smoother 'choose podcast, enter email, subscribe' flow - no explicit 'create account' needed
  - simplest option would be that each email only has a single subscription, and the only way to manage it is via the unsubscribe link in the emails (so no frontend management)
    - user goes to the site, searches/selects a podcast, enters their email
    - gets a verification email to prove they own the address - click link to activate subscription
  - not sure how to square that with supabase's auth design
  - also feels like that simple flow isn't much more complicated with a password field added, and now people have full accounts
    - even if there's nothing you can do with an account at first
    - but it seems super easy to create that frontend management w/ supabase
- got emails working to send and receive via podscript.org!
- next step: get podcast search and subscriptions working

# 11/09
- got started on the frontend with supabase - looks like the quickest/easiest way to get going

# 11/08
- Feed updating is working!
- thinking about how to put this together
  - going to put it on the pi so that it can be more persistent than on the laptop
    - API interface for adding shows, getting pending jobs, etc
  - cron job to update podcasts
- created a flask api that can list all podcasts and insert new podcasts!
  - that was easy
- next steps:
  - create jobs API to get next episode that needs processing, update status, etc
  - get it up and running on the pi
    - should do a proper env w/ dependencies tracked
  - create pipeline manager on windows laptop
    - poll the jobs API to create new transcription jobs
    - detect completed jobs and...do something about that
      - haven't really thought about how that is going to work - probably send them to the pi
      - use USB stick to archive results
      - should back them up somewhere else too
  - episode transcript email generation and sending
    - will close the loop on the end-to-end backend implementation
  - super exciting how quickly this is coming together!
    - definitely a lot still to do, but quickly approaching viable proof-of-concept

# 11/06
- want to tackle downloading in a simple way
- cron job per podcast to get the feed and add any new episodes to the database
- download script that periodically scans the episodes table for ones that need to be downloaded
  - using the `state` column on the episode table
    - 0: new - not downloaded
    - 1: file download in progress
    - 2: file download complete, unprocessed
    - 3: processed, transcript available
- thinking about how I want to manage the fact that we don't necessarily want to download/process every episode in the database
  - eg. we can add every episode a pod has ever had to the db, but don't need to process all of those
    - just want maybe the most recent one for now, and then any new ones
  - could do a per-episode flag, or something at the podcast level
    - episode-tag is more flexible to do one-offs, and doesn't seem to have much downside
    - use the `archive` column where 1 = this episode should not be processed
- 

# 11/05
- Pipeline works!!
- Researched gPodder for awhile to see how they do downloading and fille organization 
  - it seems really complicated  
  - though the file naming just seems like they use the original download name from the url
  - didn't quite figure out how they determine the podcast storage path
  - decided I probably don't need to follow too closely
  - they also have an API gpodder.net that I looked at briefly before for looking up episodes
    - website is suuuuper slow
  - still not sure how to do the search part - did have an idea to use the overcast search API, not sure if that's possible (doubt they'd notice / get mad unless this really blew up)
    - tweeted at the overcast guy a second time asking how it syncs w/ the iTunes catalog but no response

# 11/04
- Processing pipeline architecture:
  - two persistent windows processes, one started from the pyannote env that's the overall supervisor, and another started from the whisper env that's just responsible for transcription
  - using files w/ certain extensions as an rpc mechanism
- overall processing job
  - gets kicked of when there is a new episode available
  - input: url of audio file, name/identifier? (generally haven't figured out how to organize the resulting artifacts)
  - steps:
    - 1. run diarization to get speakers csv
    - 2. generate padded audio file with silence between speaking
    - 3. run transcription on modified audio file
    - 4. process speaker csv and transcription vtt into final transcript
  - 

# 11/02
- messed around awhile with doing a job queue with kafka but it's not necessary at this point
- installed mariadb on wsl, schema:
CREATE TABLE podcasts (
id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
artwork_url TEXT,
author TEXT,
backup_artwork_url TEXT,
backup_thumb_url TEXT,
category_id TEXT,
category_id_auto TEXT,
description TEXT,
e_tag TEXT,
iTunes_id TEXT,
overcast_id TEXT,
link TEXT,
release_schedule TEXT,
thumb_url TEXT,
title TEXT,
version INT UNSIGNED NOT NULL);

INSERT INTO podcasts (artwork_url, author, backup_artwork_url, backup_thumb_url, category_id, category_id_auto, description, e_tag, iTunes_id, overcast_id, link, release_schedule, thumb_url, title, version) VALUES (
"https://public.overcast-cdn.com/art/2630127?v30",
"The New York Times", 
"http://public.overcast-cdn.com.us-east-1.linodeobjects.com/art/2630127?v30", "http://public.overcast-cdn.com.us-east-1.linodeobjects.com/art/2630127_thumb?v30", "1311", 
"0", "This is what the news should sound like. The biggest stories of our time, told by the best journalists in the world. Hosted by Michael Barbaro and Sabrina Tavernise. Twenty minutes a day, five days a week, ready by 6 a.m.", "101041740", "1200361736", 
"2630127", 
"https://www.nytimes.com/the-daily", "1667382300 1667295900 1667209500 1667124000 1667037600 1666950300 1666863900 1666777500 1666691100 1666604700 1666519200 1666432800 1666345800 1666259100 1666173000 1666086300 1666000200 1665914400 1665828000 1665740700 1665654300", "https://public.overcast-cdn.com/art/2630127_thumb?v30", 
"The Daily", 0);

# 10/01
- Got a working POC for transcription and diarization over the weekend!
- now thinking about the podcast management aspect
  - ideal would be able to have a catalog of podcasts (like apple's catalog)
    - might be able to just use overcast's search API
      - `https://overcast.fm/podcasts/search_autocomplete?q=app`
  - what I need on the backend is just the feed url for each podcast I want to sync
  - can model my db after overcast's serach response records
- high-level goal:
  - users (at minimal just an email address) have subscriptions to podcasts
  - for all podcasts with subscriptions we periodically scan for new episodes
  - when a new episode is available, kick off process to transcribe it and store results
  - send transcript to subscribers
- Architecture
  - have pretty self-contained components
    - CRUD interface for users and subscriptions
    - new-episode monitor
    - transcription
- Created a simple static bootstrap landing page, set up cloudflare site
  - https://podscript.pages.dev/
- 