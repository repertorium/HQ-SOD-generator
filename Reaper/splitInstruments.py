#!/Users/jaimegarcia/miniconda3/envs/reaper/bin/python
import pathlib
import pretty_midi
import argparse

def splitInstruments(midi_data: pretty_midi.PrettyMIDI,
                     output_dir: pathlib.Path) -> list[pathlib.Path]:
    # recorre todos los instrumentos del archivo midi original y
    # escribe la info midi en ficheros independientes
    splitted_midi_filepaths = []
    for instrument in midi_data.instruments:
        # crea un nuevo objeto PrettyMidi
        instrument_midi = pretty_midi.PrettyMIDI()
        instrument_midi.instruments.append(instrument)
        # escribe
        filepath = output_dir / f'{instrument.name}.MID'
        instrument_midi.write(str(filepath))
        # agrega la ruta del fichero a la lista
        splitted_midi_filepaths.append(filepath)
    
    return splitted_midi_filepaths

def main(midi_filepath:pathlib.Path, directory:pathlib.Path):
    # crea el directorio de salida si no existe
    output_dir = directory / midi_filepath.stem
    output_dir.mkdir(parents=True,exist_ok=True)
    # importa el fichero midi
    midi_data = pretty_midi.PrettyMIDI(str(midi_filepath))
    # escribe cada instrumento midi en ficheros separados
    splitted_midi_filepaths = splitInstruments(midi_data, output_dir)
    print(','.join(str(filepath) for filepath in splitted_midi_filepaths))


if __name__ == '__main__':
    # CLI
    parser = argparse.ArgumentParser()
    parser.add_argument('-m','--midi',type=str,required=True)
    parser.add_argument('-d','--directory',type=str,required=False)
    
    args = parser.parse_args()
    midi_filepath = pathlib.Path(args.midi)
    if args.directory == None:
        directory = midi_filepath.parent
    else:
        directory = pathlib.Path(args.directory)

    main(midi_filepath,directory)