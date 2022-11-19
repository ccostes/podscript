create or replace function public.new_transcript()
returns trigger as $$
declare
  payload TEXT;
begin
  -- Send notify for podcast inserts
  payload := json_build_object('record',row_to_json(new));
  -- notify user verified
  PERFORM pg_notify('new_transcript', payload);
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_filename_updated on episodes;
create trigger on_filename_updated
  after update of filename on episodes
  for each row
  execute procedure public.new_transcript();