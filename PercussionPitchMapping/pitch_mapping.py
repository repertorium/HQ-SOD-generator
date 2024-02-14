'''
This module uses the PrettyMIDI library to remap the MIDI pitch value
for each note of untuned percussion instruments.
The remapping ensures that pitches align with the valid values of the
Spitfire BBC Symphony Orchestra Synthesizer, as specified in the
`valid_pitches.yaml` file.

Different sets of valid MIDI pitches are considered based on the
untuned percussion instrument, identified by the MIDI CC#32 value within
every single MIDI file from the database.

The remapping is performed by shifting the MIDI pitches octave-wise so
they lay within the valid range of pitches for each one of the instruments.
'''
import numpy as np
import pretty_midi
import pathlib
import yaml
from copy import deepcopy

class NoUntunedPercussionTrackFound(Exception):
    '''
    Raise this exception if no untuned percussion track is found for an
    input MIDI file
    '''
    pass

def getCC32TimeIntervals(cc32_messages:list[pretty_midi.containers.ControlChange],
                         midi_duration: float) -> np.ndarray:
    '''
    # Parameters:
    - cc32_mesagges:    list containing all the CC#32 control messagese information of
                        a midi file.
    - midi_duration:    The time duration of the midi data, in seconds.
    # Returns:
    cc32_time_intervals:    2D array containing the beginning and end time of each CC#32
                            message, efectively identifying each percussive instrument
                            time interval.
    '''
    cc32_len = len(cc32_messages)
    cc32_time_intervals = np.empty([cc32_len,2])
    # if there is more than one cc32 message
    if cc32_len > 1:
        for n in range(len(cc32_messages)):
            if n == 0:
                init_time = 0
                end_time = cc32_messages[n+1].time
            elif n == cc32_len - 1:
                init_time = cc32_messages[n].time
                end_time = midi_duration
            else:
                init_time = cc32_messages[n].time
                end_time = cc32_messages[n+1].time
            cc32_time_intervals[n,:] = np.array([init_time,end_time])
    # if not, the time interval is the whole midi file
    else:
        cc32_time_intervals[0,:] = np.array([0,midi_duration])
    
    return cc32_time_intervals

def pitch_distances(note_pitch: int,
                    instrument_valid_pitches: np.ndarray) -> np.ndarray:
    '''
    Computes the difference between the input note pitch values for every
    octave within the MIDI pitch value range and the valid pitch values.

    # Parameters:
    - note_pitch:   MIDI pitch of a note
    - instrument_valid_pitches: Valid range of pitches for the notes of the
                                considered instrument
    # Returns:
    - distances:    2D array containing the difference between the valid
                    pitches and the note pitches for every possible octave
                    within the MIDI pitch range
    '''
    rem = note_pitch%12
    octave_pitches = [*range(rem,127,12)]
    distances = np.array([abs(pitch - instrument_valid_pitches) for pitch in octave_pitches])
    
    return distances

def valid_pitch_selection(instrument_valid_pitches: np.ndarray,
                          distances: np.ndarray) -> int:
    '''
    Selects a valid pitch value based on the minimum distance of the
    array.

    # Parameters:
    - instrument_valid_pitches: Valid range of pitches for the notes of the
                                considered instrument
    - distances:    2D array containing the difference between the valid
                    pitches and the note pitches for every possible octave
                    within the MIDI pitch range
    # Returns:
    - note_valid_pitch: Valid pitch value for a MIDI note
    '''
    # select the closest valid pitch
    row, valid_pitch_index = np.unravel_index(distances.argmin(),distances.shape)
    note_valid_pitch = instrument_valid_pitches[valid_pitch_index]

    return note_valid_pitch

def note_pitch_mapping(instrument_notes: list[pretty_midi.containers.Note],
                       instrument_valid_pitches: np.ndarray) -> None:
    '''
    Changes the pitch of every note of the input list to a suitable value
    contained within the range of the valid pitches.

    # Parameters:
    - instrument_notes: list containing all the notes information of a midi
                        file.
    - instrument_valid_pitches: Valid range of pitches for the notes of the
    '''
    for note in instrument_notes:
        distances = pitch_distances(note.pitch,instrument_valid_pitches)
        note_valid_pitch = valid_pitch_selection(instrument_valid_pitches,distances)
        note.pitch = note_valid_pitch

def pitch_mapping(midi_data: pretty_midi.PrettyMIDI,
                  valid_pitches: dict) -> pretty_midi.PrettyMIDI:
    '''
    Perform pitch shifting for the notes of percussive instruments of the midi file
    so they align with the valid pitch values defined in the `valid_pitches` input 
    dictionary.
    # Parameters:
    - midi_data: The PrettyMIDI object for the midi file being processed
    - valid_pitches: A dictionary containing the valid pitch values for each
                    untuned percussion instrument
    # Returns:
    - mapped_midi_data: A copy of the original input midi data with the notes of the
                        percussive instruments mapped to the valid pitch values.
    '''
    # check if the untuned percussion track exists for this file
    instrument_names = [instrument.name for instrument in midi_data.instruments]
    if 'untunedpercussion' not in instrument_names:
        raise NoUntunedPercussionTrackFound
    # create a copy of the MIDI data
    midi_duration = midi_data.get_end_time()
    mapped_midi_data = deepcopy(midi_data)
    # get the CC#32 information
    untuned_percussion_index = instrument_names.index('untunedpercussion')
    cc32_messages = [control_change for control_change
                      in mapped_midi_data.instruments[untuned_percussion_index].control_changes
                      if control_change.number == 32]
    cc32_time_intervals = getCC32TimeIntervals(cc32_messages,midi_duration)
    # iterate for each instrument
    for n in range(len(cc32_messages)):
        # get the instrument valid pitch values based on the cc32 message value
        instrument_valid_pitches = np.array(valid_pitches[cc32_messages[n].value]['Valid_pitches'])
        # get the instrument notes. This is, notes that lay in the time interval
        # of the instrument
        instrument_notes = [note for note in mapped_midi_data.instruments[untuned_percussion_index].notes
                            if note.start > cc32_time_intervals[n,0]
                            and note.start < cc32_time_intervals[n,1]]
        # map each one of the instrument notes
        note_pitch_mapping(instrument_notes,instrument_valid_pitches)
    
    return mapped_midi_data