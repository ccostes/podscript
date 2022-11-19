import os, sys, time, logging
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

# Expects args to be a dict with keys 'audio_file' 'speakers_csv' and 'out_csv'
def pad_speakers(wav_filename, tracks, out_filename, padded_filename):
    audio = AudioSegment.from_wav(wav_filename)        
    tracks = pad_audio(audio, tracks, padded_filename)

    with open(out_filename, 'w', newline='') as f:
        field_labels = ['label', 'start', 'end', 'padded_start', 'padded_end']
        writer = csv.DictWriter(f, fieldnames=field_labels)
        writer.writeheader()
        writer.writerows(tracks)

def transcribe(filename):
    model = whisper.load_model("small.en")
    result = model.transcribe(filename, beam_size=5, best_of=5)
    return result

def main(filename, out_filename):
    # intermediate file extensions
    ext_transcription = ".vtt"
    ext_audio_padded = "_padded.wav"
    ext_speakers_csv = "_speakers.csv"
    ext_speakers_padded_csv = "_speakers_padded.csv"
    base = filename.split('.')[0]
    padded_audio = base + ext_audio_padded
    speakers_csv = base + ext_speakers_csv

    # == Diarize ==
    # pad the beginning of the input with silence - pyannote struggles with the very start
    logging.info("Prepending Silence...")
    padded_filename = "tmp_padded.wav"
    audio = AudioSegment.from_wav(audio_file)
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
    result = model.transcribe(padded_audio, beam_size=5, best_of=5)

    # 



if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    main()
