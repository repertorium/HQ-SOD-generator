# REAPER Submodule

This submodule provides a set of Python scripts for managing MIDI file synthesis using REAPER and Spitfire's BBCSO Professional sound fonts. The primary functionality is centered around the [synth.py](./synth.py) script, which is intended to be run within REAPER.

 For more information about running scripts with REAPER, refer to the official REAPER scripting documentation: https://www.reaper.fm/sdk/reascript/reascript.php#reascript_run

## Files

- `dispatcher.py`: Implements a CLI tool for managing MIDI files through a JSON list.
- `getTempoChanges.py`: A script for extracting tempo changes from MIDI files.
- `splitInstruments.py`: A script for splitting MIDI files by instruments.
- `synth.py`: The script to be run with REAPER.

## Usage

### [dispatcher.py](./dispatcher.py)
The first step in the process is to run the [dispatcher.py ](./dispatcher.py) script to scan a directory and generates a list of MIDI file paths to be synthesized. These file paths are stored in a `scanned_files.json` file. The next file to be synthesized is read from this JSON file, and once the file is processed, it is removed from the list to ensure efficient workflow progression.

[dispatcher.py ](./dispatcher.py) provides the following commands to perform these actions:

- **Scan Directory (manually called)**
    ```bash
    python dispatcher.py --directory <directory>
    ```
    Scans the specified directory for MIDI files and stores their paths in `scanned_files.json`.

- **Get the next file in the list (called within [synth.py](./synth.py))**
    ```bash
    python dispatcher.py --next 
    ```
    Automatically called within [synth.py](./synth.py) to retrieve the next MIDI file from the list for synthesis.

- **Remove the next file in the list, effectively performing a pop operation (called within [synth.py](./synth.py))**
    ```bash
    python dispatcher.py --remove
    ```
    Automatically called within [synth.py](./synth.py) after the file has been processed to remove it from the list.

### [synth.py](./synth.py)

Synthesized audio files will be stored in the directory specified by the variable `root_dir` (line 183). This variable should be set regarding the desired output directory.