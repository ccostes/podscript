import logging, datetime
from pydub import AudioSegment
from pyannote.audio import Pipeline
import whisper

import nltk
from nltk import ne_chunk, pos_tag, word_tokenize
from nltk.tree import Tree

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

def pad_audio(audio, tracks, pad_duration, out_filename):
    """
    Given an audio file and a list of tracks [speaker_label, start, end] pad the 
    audio file with silence before each track audio segment and return the track list
    with the start/end time of each track in the padded audio file
    """
    spacer = AudioSegment.silent(duration=pad_duration)
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

def merge_dz_segments(tracks, segments):
    transcript = []
    label_iter = iter(tracks)
    # Add first label
    next_track = next(label_iter)
    # transcript.append(f"[Speaker {next_track['label'][8:]}]\n")
    block = {'speaker': next_track['label'], 'time': 0, 'text': ""}
    next_track = next(label_iter)
    # Iterate through transcribed segments
    for caption in segments:
        if len(caption['text']) == 0:
            continue
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
                    block['text'] += caption['text']
                    transcript.append(block)
                    block = {
                        'speaker': next_track['label'],
                        'time': next_track['start'],
                        'text': ""
                        }
                else: 
                    # majority in next track, print next track label first, then caption
                    transcript.append(block)
                    block = {
                        'speaker': next_track['label'],
                        'time': next_track['start'],
                        'text': ""
                        }
                    block['text'] += caption['text']
                try:
                    next_track = next(label_iter)
                except StopIteration:
                    next_track = None
            else:
                # whole caption in current track, just append it
                block['text'] += caption['text']
        else:
            # no more tracks, just append the rest of the captions 
            block['text'] += caption['text']
    transcript.append(block)
    return transcript

def detect_speaker_identification(text):
    nltk_results = ne_chunk(pos_tag(word_tokenize(text)))
    for i, result in enumerate(nltk_results):
        if type(result) == Tree and result.label() == 'PERSON':
            name = result
            if nltk_results[i-2][0] == "I":
                if nltk_results[i-1][0] == "am" or nltk_results[i-1][0] == "'m":
                    name = []
                    for nltk_result_leaf in result.leaves():
                        name.append(nltk_result_leaf[0])
                    return name
    return None

def gen_transcript(tracks, segments):
    speaker_lines = []
    lines = merge_dz_segments(tracks=tracks, segments=segments)
    speaker_map = {}
    speakers = {}
    for l in lines:
        speaker_id = l['speaker']
        if speaker_id not in speaker_map:
            id = len(speaker_map)
            speaker_map[speaker_id] = id
            speakers[id] = {
                'detected':False,
                'name': [f"Speaker {len(speakers) + 1}"]
            }
        id = speaker_map[speaker_id]
        if not speakers[id]['detected']:
            # See if speaker identified themselves
            name = detect_speaker_identification(l['text'])
            if name is not None:
                # Found a name!
                speakers[id]['detected'] = True
                speakers[id]['name'] = name
        # append line to transcript
        line = {
            'speaker': id,
            'text': l['text']
        }
        speaker_lines.append(line)
    transcript = {
        'speakers': speakers,
        'lines': speaker_lines,
    }
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
    # tracks = pad_audio(audio=audio, tracks=tracks, pad_duration=spacermilli, out_filename=padded_audio)
    tracks = pad_audio(audio=audio, tracks=tracks, pad_duration=200, out_filename=padded_audio)

    # == Transcribe ==
    model = whisper.load_model("small.en")
    result = model.transcribe(padded_audio, beam_size=5, best_of=5)
    segments = result["segments"]

    # == Generate Transcript ==
    transcript = gen_transcript(tracks=tracks, segments=segments)
    return transcript

def main():
    import json
    transcript = transcribe(filename="daily_clip.wav")
    print(json.dumps(transcript, indent = 2))

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
