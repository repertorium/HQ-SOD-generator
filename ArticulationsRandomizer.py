'''
This module generates random articulation intervals within an input MIDI file
according to the probabilities specified in the `articulations.yaml` file.
'''

import pathlib
import yaml
import random
import pretty_midi
import numpy as np

def loadYaml(yaml_file : pathlib.Path = pathlib.Path(__file__).parent / 'articulations.yaml') -> dict:
    with open(yaml_file, 'r') as f:
        articulations = yaml.load(f,Loader=yaml.FullLoader)

    return articulations

def getRandomArticulationIntervals(instrument_articulations: dict,
                                   midi_data_end_time: float,
                                   default_upper_limit: int = 2,
                                   extra_duration: float = 120,
                                   upper_limit_increasing_ratio: int = 1) -> tuple[list[str],list[float]]:
    '''
    Randomly generates a set of articulation intervals for a given instrument.

    The total amount of articulation intervals is computed randomly and
    depends on the midi file length. By default, the upper limit of 
    intervals is 2 and increases by one for every `extra_duration` extra
    minutes of duration of the MIDI file. The lower limit is always 1.

    For example if `extra_duration` is set to 2 and `upper_limit_increasing_ratio`
    is set to 1, a MIDI file with 3:59 minutes of duration will have the maximum
    number of possible articulation intervals set on 3, exactly the same for another
    file with 2:30 minutes of duration. That doesn't mean that 3 articulations
    intervals will be enforced because the number of articulation intervals is
    randomly set.

    # Parameters:
    - instrument_articulations: Dictionary containing all the possible articulations
                                for the processed instrument
    - midi_data_end_time: End time of the input midi file in seconds
    - default_upper_limit: Upper limit for the number of articulation intervals to
                           generate. Even if file is shorter than
                           `default_time_limit`
    - extra_duration: Time duration in seconds that implies adding a
                     `upper_limit_increasing_ration` extra articulation interval.
    - upper_limit_increasing_ratio: How many extra articulation intervals to add
                                    for each extra `extra_duration` minutes of the
                                    processed MIDI file
    # Returns: 
    - articulations: List of articulations for each of the generated intervals
    - start_times: List of start times for each of the generated intervals
    '''
    # randomly establish a total number of articulation intervals
    extra_intervals = int(np.ceil((midi_data_end_time/extra_duration -1))*upper_limit_increasing_ratio)
    upper_limit = default_upper_limit + extra_intervals
    total_articulation_interval = random.randint(1,upper_limit)
    # compute start time for each of the articulation intervals (first one starts at 0 seconds)
    start_times = random.sample(np.linspace(0,midi_data_end_time,int(midi_data_end_time)).tolist(),k=total_articulation_interval-1)
    start_times.sort()
    start_times.insert(0,0.0)
    # assign an articulation for each of the articulation intervals based on a cummulative approach
    articulations = []
    for n in range(total_articulation_interval):
        # computes a random value between 0 (0% prob) and 1 (100% prob)
        random_value = random.uniform(0,1)
        cumulative_prob = 0
        # iterates over all the possible articulations for this instrument
        for articulation in instrument_articulations:
            cumulative_prob += instrument_articulations[articulation]['Probability']
            if random_value <= cumulative_prob:
                articulations.append(articulation)
                break
    
    return articulations,start_times

def insertInstrumentArticulationIntervals(instrument_articulations: dict,
                                          instrument_midi_data: pretty_midi.PrettyMIDI,
                                          default_upper_limit: int = 2,
                                          extra_duration: float = 120,
                                          upper_limit_increasing_ratio: int = 1) -> None:
    '''
    Insert articulation intervals for one instrument contained in a MIDI file.

    The articulations are expressed in terms of the MIDI CC#32 controller value specified
    in the `articulations.yaml` file.

    # Parameters
    - instrument_articulations: Dictionary containing all the possible articulations
                                for the processed instrument
    - midi_data_end_time: End time of the input midi file in seconds
    - default_upper_limit: Upper limit for the number of articulation intervals to
                           generate. Even if file is shorter than
                           `default_time_limit`
    - extra_duration: Time duration in seconds that implies adding a
                     `upper_limit_increasing_ration` extra articulation interval.
    - upper_limit_increasing_ratio: How many extra articulation intervals to add
                                    for each extra `extra_duration` minutes of the
                                    processed MIDI file
    '''
    # randomly compute articulation intervals for this instrument
    midi_data_end_time = instrument_midi_data.get_end_time()
    articulations, start_times = getRandomArticulationIntervals(instrument_articulations=instrument_articulations,
                                                                midi_data_end_time=midi_data_end_time,
                                                                default_upper_limit=default_upper_limit,
                                                                extra_duration=extra_duration,
                                                                upper_limit_increasing_ratio=upper_limit_increasing_ratio)
    # insert controller events 
    for articulation, start_time in zip(articulations,start_times):
        # get the CC#32 value for the given articulation
        value = instrument_articulations[articulation]['CC#32']
        # create a new control change envent
        new_control_change = pretty_midi.ControlChange(number=32, value=value, time=start_time)
        # adds the new control change event
        instrument_midi_data.control_changes.append(new_control_change)

def insertArticulationIntervals(seed:int,
                                articulations: dict,
                                midi_data: pretty_midi.PrettyMIDI,
                                default_upper_limit: int = 2,
                                extra_duration: float = 120,
                                upper_limit_increasing_ratio: int = 1) -> None:
    '''
    Insert articulation intervals for the processing MIDI file

    # Parameters:
    - seed: Seed for random number generation
    - articulations: Dictionary containing all the possible articulations. This is really the
                    read data from the `articulations.yaml` file.
    - midi_data: The midi data representing a midi file obtained from the
                 `pretty_midi.PrettyMIDI` function.
    - default_upper_limit: Upper limit for the number of articulation intervals to
                           generate. Even if file is shorter than
                           `default_time_limit`
    - extra_duration: Time duration in seconds that implies adding a
                     `upper_limit_increasing_ration` extra articulation interval.
    - upper_limit_increasing_ratio: How many extra articulation intervals to add
                                    for each extra `extra_duration` minutes of the
                                    processed MIDI file
    '''
    # get the name of the instruments for which there are articulations defined
    instrument_names = list(map(lambda string: string.lower(),articulations.keys()))
    # set the randomizer state
    random.seed(seed)
    # iterates over the instruments contained in the midi file
    for instrument in midi_data.instruments:
        # if the instrument is not within the instrument list skip the processing
        instrument_name = instrument.name.split('_')[0].lower()
        if instrument_name not in instrument_names:
            continue
        # get the instrument articulations
        instrument_articulations = articulations[instrument_name]
        # insert articulation intervals for this instrument
        insertInstrumentArticulationIntervals(instrument_articulations = instrument_articulations,
                                              instrument_midi_data = instrument,
                                              default_upper_limit = default_upper_limit,
                                              extra_duration = extra_duration,
                                              upper_limit_increasing_ratio = upper_limit_increasing_ratio)