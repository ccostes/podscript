create or replace function public.new_episode()
returns trigger as $$
declare
  payload TEXT;
begin
  -- Query subscriptions for podcast and set pending_publish_id if it is not currently set
  UPDATE public.subscriptions 
    SET pending_publish_id = new.id 
    WHERE podcast_id = new.podcast_id 
        AND pending_publish_id IS NULL;
  return new;
  
  -- Notify on new_episode
  payload := json_build_object('record',row_to_json(new));
  -- notify user verified
  PERFORM pg_notify('new_episode', payload);
end;
$$ language plpgsql security definer;

drop trigger if exists on_episode_inserted on public.episodes;
create trigger on_episode_inserted
  after insert on public.episodes
  for each row
  execute procedure public.new_episode();