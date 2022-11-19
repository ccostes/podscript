import logging
from pydub import AudioSegment
from pyannote.audio import Pipeline
import whisper

# spacer duration (ms)
spacermilli = 2000

def prepend_silence(audio):
    # create 2-secs of silence to use as a spacer
    spacer = AudioSegment.silent(duration=spacermilli)
    audio = spacer.append(audio, crossfade=0)
    return audio

def get_diarization(file):
    pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization@2.1', use_auth_token="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")
    pipeline._segmentation.progress_hook = print
    dz = pipeline(file)
    return dz

def get_speakers(dz):
    """
    Given a diarization, merge consecutive tracks for the same speaker and return
    a list of [speaker_label, start, end] where start and end are in seconds, compensating
    for the `spacermilli` ms padding.
    """
    tracks = []
    for t, _, speaker in dz.itertracks(yield_label=True):
        # remove the padding time added to the beginning of the file
        start, end = t.start - spacermilli / 1000, t.end - spacermilli / 1000
        # print(t, speaker)
        if len(tracks) > 0 and tracks[-1]['label'] == speaker:
            # same speaker as previous track, update existing track end
            tracks[-1]['end'] = end
        else:
            tracks.append({'label': speaker, 'start': start, 'end': end})
    return tracks

def pad_audio(audio, tracks, out_filename):
    """
    Given an audio file and a list of tracks [speaker_label, start, end] pad the 
    audio file with silence before each track audio segment and return the track list
    with the start/end time of each track in the padded audio file
    """
    spacer = AudioSegment.silent(duration=spacermilli)
    sounds = AudioSegment.silent(duration=0)
    for t in tracks:
        # append silence padding
        sounds = sounds.append(spacer, crossfade=0)
        
        # add track audio
        start, end =  float(t['start']) * 1000, float(t['end']) * 1000
        # record padded track start time
        t['padded_start'] = len(sounds) / 1000
        # append track
        sounds = sounds.append(audio[start:end], crossfade=0)
        # record end time
        t['padded_end'] = len(sounds) / 1000
    sounds.export(out_filename, format="wav")
    return tracks

def gen_transcript(tracks, segments):
    transcript = []

    label_iter = iter(tracks)
    # Add first label
    next_track = next(label_iter)
    # transcript.append(f"[Speaker {next_track['label'][8:]}]\n")
    block = {'speaker': next_track['label'], 'time': 0, 'text': []}
    next_track = next(label_iter)

    for caption in segments:
        caption_start_sec = caption['start']
        caption_end_sec = caption['end']
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
                    block['text'].append(caption['text'])
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
                    block['text'].append(caption['text'])
                try:
                    next_track = next(label_iter)
                except StopIteration:
                    next_track = None
            else:
                # whole caption in current track, just append it
                block['text'].append(caption['text'])
        else:
            # no more tracks, just append the rest of the captions 
            block['text'].append(caption['text'])
    return transcript

def transcribe(filename):
    # intermediate file extensions
    ext_audio_padded = "_padded.wav"
    base = filename.split('.')[0]
    padded_audio = base + ext_audio_padded

    # == Diarize ==
    # pad the beginning of the input with silence - pyannote struggles with the very start
    logging.info("Prepending Silence...")
    padded_filename = "tmp_padded.wav"
    audio = AudioSegment.from_wav(filename)
    prepend_silence(audio).export(padded_filename, format="wav")

    # perform diarization
    print(f"Diarizing {padded_filename} ...")
    dz = get_diarization(padded_filename)

    # extract speaker tracks
    tracks = get_speakers(dz)

    # == Pad Speakers ==
    pad_audio(audio=audio, tracks=tracks, out_filename=padded_audio)

    # == Transcribe ==
    model = whisper.load_model("small.en")
    result = model.transcribe(filename, beam_size=5, best_of=5)
    segments = result["segments"]

    # == Generate Transcript ==
    transcript = gen_transcript(tracks=tracks, segments=segments)
    return transcript

def main():
    transcript = transcribe(filename="daily_clip.wav")
    print(transcript)

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
