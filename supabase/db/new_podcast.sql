create or replace function public.new_podcast()
returns trigger as $$
declare
  payload TEXT;
begin
  -- Send notify for podcast inserts
  payload := json_build_object('record',row_to_json(new));
  -- notify user verified
  PERFORM pg_notify('new_podcast', payload);
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_podcasts_insert on public.podcasts;
create trigger on_podcasts_insert
  after insert on public.podcasts
  for each row
  execute procedure public.new_podcast();