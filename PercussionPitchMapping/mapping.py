#!/Users/jaimegarcia/miniconda3/envs/midi/bin/python
import pretty_midi
import yaml
import numpy as np
import matplotlib.pyplot as plt
import pathlib
from tqdm import tqdm
from pitch_mapping import pitch_mapping, NoUntunedPercussionTrackFound

if __name__ == '__main__':
    working_parentdir = pathlib.Path(__file__).parent.resolve()
    output_parent_dir = pathlib.Path('/Users/jaimegarcia/Desktop/BBCSO/targetMIDI/MIDI/expressive_mapped_repetidos_v2').resolve()
    valid_pitches_filepath = working_parentdir /'valid_pitches.yaml'
    target_midi_dirpath = pathlib.Path('/Users/jaimegarcia/Desktop/BBCSO/targetMIDI/MIDI/expressive_repetidos_v2').resolve()
    with open(valid_pitches_filepath,'r') as f:
        valid_pitches = yaml.safe_load(f)
    midifiles = [file.resolve() for file in target_midi_dirpath.glob('*.mid')]
    output_dir = output_parent_dir / midifiles[0].parent.name
    output_dir.mkdir(parents=True,exist_ok=True)
    for midifile in tqdm(midifiles,total=len(midifiles)):
        midi_data = pretty_midi.PrettyMIDI(str(midifile))
        try:
            mapped_midi_data = pitch_mapping(midi_data,valid_pitches)
            output_filepath = output_dir / midifile.name
            print(f'Escribiendo fichero de audio {str(output_filepath)}')
            mapped_midi_data.write(output_filepath)
        except NoUntunedPercussionTrackFound:
            print(f'El fichero {str(midifile)} no tiene instrumentos percusivos')
            continue
        except KeyError:
            print(f'Error de formateo en el fichero {str(midifile)}')
            continue