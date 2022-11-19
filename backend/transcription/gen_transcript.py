import sys, logging, time, csv, datetime, json
import webvtt

def get_sec(time_str):
    """Get seconds from time in format HH:MM:SS.ms."""
    h, m, s = time_str.split(':')
    s, ms = s.split('.')
    # print(time_str.split(':'))
    return int(h) * 3600 + int(m) * 60 + int(s) + (int(ms) / 1000)

def get_timestamp(sec):
    """Get HH:MM:SS.ms timestamp from seconds."""
    return str(datetime.timedelta(seconds=sec))

def gen_transcript(tracks, vtt_file, out_filename):
    transcript = []

    label_iter = iter(tracks)
    # Add first label
    next_track = next(label_iter)
    # transcript.append(f"[Speaker {next_track['label'][8:]}]\n")
    block = {'speaker': next_track['label'], 'time': 0, 'text': []}
    next_track = next(label_iter)

    for caption in webvtt.read(vtt_file):
        caption_start_sec = get_sec(caption.start)
        caption_end_sec = get_sec(caption.end)
        # label is none if we run out, otherwise check if the label should be inserted
        if next_track is not None:
            next_track_start = float(next_track['padded_start'])
            next_track_end = float(next_track['padded_end'])
            # check whether the current caption is more in the previous or next track
            if caption_end_sec > next_track_start:
                caption_len = caption_end_sec - caption_start_sec
                pct_in_curr_track = (next_track_start - caption_start_sec) / caption_len
                if pct_in_curr_track > 0.5:
                    # majority in current track, print caption first then next track label
                    block['text'].append(caption.text)
                    transcript.append(block)
                    block = {
                        'speaker': next_track['label'],
                        'time': next_track['start'],
                        'text': []
                        }
                else: 
                    # majority in next track, print next track label first, then caption
                    transcript.append(block)
                    block = {
                        'speaker': next_track['label'],
                        'time': next_track['start'],
                        'text': []
                        }
                    block['text'].append(caption.text)
                try:
                    next_track = next(label_iter)
                except StopIteration:
                    next_track = None
            else:
                # whole caption in current track, just append it
                block['text'].append(caption.text)
        else:
            # no more tracks, just append the rest of the captions 
            block['text'].append(caption.text)
    return transcript

def speaker_label(speaker):
    return f"[Speaker {speaker[8:]}]"

def write_transcript(transcript, outfile):
    json_outfile = outfile + '.json'
    text_outfile = outfile + '.txt'
    with open(json_outfile, "w") as f:
        json.dump(transcript, f)
    with open(text_outfile, 'w') as f:
        for block in transcript:
            if len(block['text']) == 0:
                continue
            text = ""
            for line in block['text']:
                if len(text) > 0:
                    if text[-1] == '.' or text[-1] == '?':
                        text += "\n"
                    elif text[-2:] != "\n":
                        text += " "
                    text += line
                else:
                    text += line
            f.write(f"\n\n[Speaker {block['speaker'][8:]} {get_timestamp(float(block['time']))}]\n")
            f.write(text)

# Expects args dict with keys 'speakers_padded_csv' 'vtt_file' 'output_filename'
def transcribe(job_info):
    csv_filename = job_info['speakers_padded_csv']
    vtt_file = job_info['vtt_file']
    out_filename = job_info['output_filename']
    logging.info(f"Generating Transcript! output file: {out_filename}")

    # get speaker tracks list
    with open(csv_filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        tracks = list(reader)
    
    transcript = gen_transcript(tracks, vtt_file, out_filename)
    write_transcript(transcript, outfile=out_filename)

def main():
    if len(sys.argv) != 3:
        print(f"Usage: transcript.py <csv file> <vtt file> (got: {sys.argv})")
        return
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    csv_filename = sys.argv[1]
    vtt_file = sys.argv[2]
    out_filename = vtt_file.split('.')[0] + "_transcript"
    transcribe({
        'speakers_padded_csv': csv_filename,
        'vtt_file': vtt_file,
        'output_filename': out_filename
    })

if __name__ == '__main__':
   main()