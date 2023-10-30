'''
This module generates random tempo intervals within an input MIDI file
following the statistical pattern of a normal distribution.
'''
import pretty_midi
import random
import numpy as np
from typing import Union

def getRandomTempoIntervals(seed: int,
                            midi_data_end_time: float,
                            mean: int,
                            deviation: int,
                            min_tempo_intervals:int,
                            max_tempo_intervals:int) -> tuple[list[int],list[float]]:
    '''
    Randomly generates a set of tempo intervals.

    Tempo values are computed randomly following a normal distribution
    statistical pattern, with `mean` being the average tempo of the intervals.
    Lower and upper values a aproximated by mean - 3*`deviation` and
    mean + 3*`deviation`,respectively.

    # Parameters:
    - seed: Seed for random number generation
    - midi_data_end_time: End time of the input midi file
    - mean: Mean tempo value of the generated intervals
    - deviation: Desired standard deviation of the tempo intervals
    - min_tempo_intervals: Minimum random tempo intervals to generate
    - max_tempo_intervals: Maximum random tempo intervals to generate
    # Returns: 
    - tempo_values: List of tempo values for each of the generated intervals
    - start_times: List of start times for each of the generated intervals
    '''
    random.seed(seed)
    # randomly establish a total number of tempo intervals
    tempo_intervals = random.randint(min_tempo_intervals,max_tempo_intervals)
    np.random.seed(seed % 2**32)
    # compute tempos
    tempo_values = np.int16(deviation*np.random.randn(tempo_intervals) + mean)
    # compute start time for each of the tempo intervals
    start_times = random.sample(np.linspace(0,midi_data_end_time,100).tolist(),k=tempo_intervals) 
    start_times.sort()

    return tempo_values.tolist(), start_times


def insertTempoChanges(midi_data: pretty_midi.PrettyMIDI,
                       tempo_values:Union[float,list],
                       start_times:Union[float,list]) -> None:
    '''
    Inserts tempo intervals in a MIDI file at the specified start times.
    
    `start_times` should be ordered from least to greatest.

    # Parameters:
    - midi_data: Midi data from a midi file modeled as a PrettyMidi object
    - tempo_values: List of tempo values for each of the intervals
    - start_times: List of start times for each of the intervals
    '''

    if isinstance(tempo_values,list) and isinstance(start_times,list):
        # iterate over every tempo value and start time
        for new_tempo_value, new_tempo_start_time in zip(tempo_values,start_times):
            # get the midi file duration
            midi_duration = midi_data.get_end_time()
            # get number of beats from interval start time to the end
            n_beats = len(midi_data.get_beats(new_tempo_start_time))
            # compute new duration
            new_duration = n_beats/new_tempo_value*60 + new_tempo_start_time
            # insert tempo change
            midi_data.adjust_times([0,new_tempo_start_time,midi_duration],[0,new_tempo_start_time,new_duration])