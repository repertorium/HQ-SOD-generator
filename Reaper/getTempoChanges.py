#!/Users/jaimegarcia/miniconda3/envs/reaper/bin/python
import pathlib
import pretty_midi
import argparse

def main(midi_filepath:pathlib.Path):
    # crea una lista de tuplas (change_time,tempo_value)
    times_tempo_pairs = []
    midi_data = pretty_midi.PrettyMIDI(str(midi_filepath))
    change_times,tempo_values = midi_data.get_tempo_changes()
    for change_time,tempo_value in zip(change_times,tempo_values):
        times_tempo_pairs.append((change_time,tempo_value))
    # stdout
    print(times_tempo_pairs)

if __name__ == '__main__':
    # CLI
    parser = argparse.ArgumentParser()
    parser.add_argument('-m','--midi',type=str,required=True)
    
    args = parser.parse_args()
    midi_filepath = pathlib.Path(args.midi)

    main(midi_filepath)