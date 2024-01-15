#!/Users/jaimegarcia/miniconda3/envs/midi/bin/python

import argparse
import pathlib
import Utils
import TempoRandomizer
import DynamicsRandomizer
import ArticulationsRandomizer
import pretty_midi
import numpy as np

def processMIDI(midi_data : pretty_midi.PrettyMIDI,
                seed: int) -> None:
    # insert tempo intervals
    tempo_values, start_times= TempoRandomizer.getRandomTempoIntervals(seed,midi_data.get_end_time(),mean=120,deviation=20,
                        min_tempo_intervals=4,max_tempo_intervals=10)
    TempoRandomizer.insertTempoChanges(midi_data,tempo_values,start_times)
    # random dynamic intervals
    DynamicsRandomizer.insertDynamicIntervals(seed,midi_data)
    # random articulation intervals
    ArticulationsRandomizer.insertArticulationIntervals(seed=seed,
                                                    articulations = ArticulationsRandomizer.loadYaml(),
                                                    midi_data = midi_data)

def main(source_dir : pathlib.Path,
         destination_dir: pathlib.Path) -> None:
    
    destination_dir.mkdir(parents=True,exist_ok=True)
    # Crawl through source directory
    for file in source_dir.glob('*'):
        if file.suffix not in ['.mid','.MID']:
            continue
        # if file is midi, process it
        try:
            print(f'Processing {str(file)}...')
            midi_data = pretty_midi.PrettyMIDI(str(file))
            seed = Utils.computeSeed(file.stem)
            processMIDI(midi_data,seed)
            # save to output directory
            midi_data.write(str(destination_dir / file.name))
            print(f'Saved output file {destination_dir / file.name }\n')
        # if errors occur, skip this iteration
        except Exception as e:
            print(f'Error processing file {file.name}:\n{e}')
            continue
if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-s','--source',type=str,required=True)
    parser.add_argument('-d','--destination',type=str,required=True)

    args = parser.parse_args()

    main(source_dir = pathlib.Path(args.source),
         destination_dir = pathlib.Path(args.destination))