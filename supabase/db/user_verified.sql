select * from tokens;

create or replace function public.user_verified()
returns trigger as $$
declare
  podcast_id INT;
begin
  -- Create token
  insert into public.tokens (id) values (new.id);

  -- Get ID of podcast if we already have it in our table
  select id into podcast_id from public.podcasts 
    where feed_url = new.raw_user_meta_data->'user_metadata'->'podcast'->>'feed_url';
  
  -- Insert podcast record if we don't have it
  IF podcast_id IS NULL THEN
    INSERT INTO public.podcasts (apple_id, feed_url) VALUES (
      new.raw_user_meta_data->'user_metadata'->'podcast'->>'apple_id',
      new.raw_user_meta_data->'user_metadata'->'podcast'->>'feed_url'
    );
    -- Get the id of the newly created podcast record
    select id into podcast_id from public.podcasts 
      where feed_url = new.raw_user_meta_data->'user_metadata'->'podcast'->>'feed_url';
  END IF;
  

  -- Create subscription
  insert into public.subscriptions (user_id, podcast_id, podcast_apple_id, feed_url) values (
    new.id,
    podcast_id,
    new.raw_user_meta_data->'user_metadata'->'podcast'->>'apple_id',
    new.raw_user_meta_data->'user_metadata'->'podcast'->>'feed_url'
    );

  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_updated on auth.users;
create trigger on_auth_user_updated
  after update of email_confirmed_at on auth.users
  for each row
  when (OLD.email_confirmed_at IS DISTINCT FROM NEW.email_confirmed_at)
  execute procedure public.user_verified();