'''
This module generates random dynamics intervals within an input MIDI file by
mapping dynamic marks to MIDI velocity values.

The array of dynamics considered encompasses from pianississimo to fortississimo
and also gradual transitions as crescendos and diminuendos. 
'''
import pretty_midi
import random
import numpy as np

def getRandomDynamicIntervals(seed:int ,
                              midi_data_end_time: float,
                              dynamic_velocity_map: dict,
                              min_dynamic_intervals:int,
                              max_dynamic_intervals:int) -> tuple[list[str],list[float]]:
    '''
    Randomly generates a set of dynamic intervals without gradual transitions.

    # Parameters:
    - seed: Seed for random number generation
    - midi_data_end_time: End time of the input midi file
    - dynamic_velocity_map: Dictionary with its keys being dynamic marks (piano, forte, ...)
    and its values beign lists with MIDI velocity values considered to belong to the corresponding
    dynamic
    - min_dynamic_intervals: Minimum random dynamic intervals to generate
    - max_dynamic_intervals: Maximum random tempo intervals to generate
    # Returns:
    - dynamics: List of dynamic marks for each of the generated intervals
    - start_times: List of start times for each of the generated intervals
    '''
    random.seed(seed)
    # randomly establish a total number of dynamic intervals
    total_dynamic_intervals = random.randint(min_dynamic_intervals,max_dynamic_intervals)
    # randomly set a dynamic mark for each interval 
    # two adjacent intervals cannot have the same dynamic
    dynamics = []
    while len(dynamics) < total_dynamic_intervals:
        dynamic = random.choice(list(dynamic_velocity_map.keys()))
        if len(dynamics) == 0:
            dynamics.append(dynamic)
            continue
        if dynamic != dynamics[-1]:
            dynamics.append(dynamic)
    # randomly computes the start time for each dynamic interval
    start_times = random.sample(np.linspace(0,midi_data_end_time,100).tolist(),k=total_dynamic_intervals-1) 
    start_times.sort()
    # first dynamic interval starts at time 0
    start_times.insert(0,0)

    return dynamics,start_times

def addRandomDyamicTransitions(seed: int,
                               dynamic_velocity_map: dict,
                               dynamics: list[str],
                               start_times: list[float],
                               max_transitions_percentage: float,
                               transition_min_duration: int,
                               transition_max_duration: int) -> None:
    '''
    Randomly adds transitions between adjacent dynamic intervals.
    Transitions may be abrupt (no further operations needed) or gradual
    (crescendos or diminuendos).
    The number of gradual transitions will not be grater than the `max_transitions_percentage`
    value.

    Transitions and start_times are inserted in the same input lists, returning nothing.

    # Parameters:
    - seed: Seed for random number generation
    - dynamic_velocity_map: Dictionary with its keys being dynamic marks (piano, forte, ...)
    and its values beign lists with MIDI velocity values considered to belong to the corresponding
    dynamic
    - dynamics: List of dynamic marks for each of the dynamic intervals
    - start_times: List of start times for each of the dynamic intervals
    - max_transitions_percentage: The maximum number of gradual transitions that can be inserted.
    Its value is expressed within 0 and 1
    - transition_min_duration: The minimum duration that a gradual tansition may have
    - transition_max_duration: The maximum duration that a gradual tansition may have
    '''
    random.seed(seed)
    # randomly establish the total number of gradual transitions
    max_transitions = int(np.ceil(max_transitions_percentage*len(dynamics)))
    n_transitions = random.randint(0,max_transitions)
    # randomly select indexes where this transitions are inserted
    # selected indexes cant be 0 nor -1 and cant be consecutive
    # (transtions occur between two different dynamic intervals)
    transition_indexes = random.sample([*range(1,len(dynamics)-1)],k=n_transitions)
    transition_indexes.sort()
    # ensure no consecutive indexes
    while (abs(np.diff(transition_indexes)) == 1).any():
        transition_indexes = random.sample([*range(1,len(dynamics)-1)],k=n_transitions)
        transition_indexes.sort()
    # randomly computes each gradual transition duration
    transition_durations = random.sample([*range(transition_min_duration,transition_max_duration)],k=n_transitions)
    # insert gradual transitions in the dynamic list and adjust start times accordingly
    for n,(transition_index,transition_duration) in enumerate(zip(transition_indexes,transition_durations)):
        # lists increase with each iteration, compute transition_index keeping this in mind
        transition_index += n
        # determine if transition is crescendo or diminuendo
        prev_dynamic = dynamics[transition_index-1]
        next_dynamic = dynamics[transition_index]
        prev_dynamic_max_velocity = dynamic_velocity_map[prev_dynamic].max()
        next_dynamic_min_velocity = dynamic_velocity_map[next_dynamic].min()
        if prev_dynamic_max_velocity > next_dynamic_min_velocity:
            transition = 'diminuendo'
        else:
            transition = 'crescendo'
        # set the start time of the transition and insert it in the list
        next_dynamic_start_time = start_times[transition_index]
        dynamics.insert(transition_index,transition)
        # adjust start times
        # if not negative, transition should occur within two adjacent intervals
        if next_dynamic_start_time - transition_duration/2 > 0:
            start_times[transition_index] = next_dynamic_start_time - transition_duration/2
            start_times.insert(transition_index+1,next_dynamic_start_time + transition_duration/2)
        # if negative, transition duration extends into next interval duration
        else:
            start_times[transition_index] = next_dynamic_start_time
            start_times.insert(transition_index+1,next_dynamic_start_time + transition_duration)

def insertDynamicIntervals(seed:int,
                           midi_data: pretty_midi.PrettyMIDI,
                           min_dynamic_intervals:int = 3,
                           max_dynamic_intervals:int = 10,
                           max_transitions_percentage: float = 0.3,
                           transition_min_duration: int = 5,
                           transition_max_duration: int = 20) -> None:
    '''
    Randomly inserts dynamic intervals in a MIDI file.

    New dynamic information is inserted in the input MIDI file, returning nothing.
    # Parameters:
    - seed: Seed for random number generation
    - midi_data: Midi data from a midi file modeled as a PrettyMidi object
    - min_dynamic_intervals: Minimum random dynamic intervals to generate. Defaults to 3
    - max_dynamic_intervals: Maximum random tempo intervals to generate. Defaults to 10.
    - max_transitions_percentage: The maximum number of gradual transitions that can be inserted.
    Its value is expressed within 0 and 1. Defaults to 0.3
    - transition_min_duration: The minimum duration that a gradual tansition may have. Defaults to
    5 seconds.
    - transition_max_duration: The maximum duration that a gradual tansition may have. Defaults to
    5 seconds.
    '''
    # Mapeo dinamicas - velocity
    dynamic_velocity_map = {
    'ppp':np.arange(0,16),
    'pp':np.arange(16,32),
    'p':np.arange(32,48),
    'mp':np.arange(48,64),
    'mf':np.arange(64,80),
    'f':np.arange(80,96),
    'ff':np.arange(96,112),
    'fff':np.arange(112,128),
    }
    # random dynamic intervals
    dynamics, start_times = getRandomDynamicIntervals(seed,midi_data.get_end_time(),dynamic_velocity_map,
                              min_dynamic_intervals,max_dynamic_intervals)
    # random transitions
    addRandomDyamicTransitions(seed,dynamic_velocity_map,dynamics,start_times,
                               max_transitions_percentage,transition_min_duration, transition_max_duration)
    # print dynamic marks and start times for each interval
    for start_time, dynamic in zip(start_times,dynamics):
        print(f'{round(start_time,2)} segs:\t{dynamic}')
    # enforce midi velocity to each note
    random.seed(seed)
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            # check which interval the note belongs to and get the dynamic mark
            interval_index = np.where(np.array(start_times) <= note.start)[0][-1]
            dynamic = dynamics[interval_index]
            # if is not a gradual transition, assign a random velocity value within
            # the mapped interval
            if dynamic != 'diminuendo' and dynamic != 'crescendo':
                new_velocity = random.choice(dynamic_velocity_map[dynamic].tolist())
            # if it is a gradual transition, linear approximation
            else:
                # compute time increase from previous to next dynamic interval
                prev_interval_dynamic = dynamics[interval_index - 1]
                next_interval_dynamic = dynamics[interval_index + 1]
                prev_interval_end_time = start_times[interval_index]
                next_interval_start_time = start_times[interval_index+1]
                delta_time = next_interval_start_time - prev_interval_end_time
                # Compute slope depending if transition is diminuendo or crescendo
                prev_interval_min_velocity = dynamic_velocity_map[prev_interval_dynamic].min()
                prev_interval_max_velocity = dynamic_velocity_map[prev_interval_dynamic].max()
                next_interval_min_velocity = dynamic_velocity_map[next_interval_dynamic].min()
                next_interval_max_velocity = dynamic_velocity_map[next_interval_dynamic].max()
                if dynamic == 'diminuendo':
                    # negative slope
                    slope = (next_interval_min_velocity - prev_interval_max_velocity)/delta_time
                    # y-intercept (velocity value at the start of the transition)
                    y_intercept = prev_interval_max_velocity
                elif dynamic == 'crescendo':
                    # positive slope
                    slope = (next_interval_max_velocity - prev_interval_min_velocity)/delta_time
                    # y-intercept (velocity value at the start of the transition)
                    y_intercept = prev_interval_min_velocity
                # compute velocity for the note, ensures interger
                new_velocity = int(round(slope*(note.start - prev_interval_end_time) + y_intercept))
            # enforce midi velocity to note
            note.velocity = new_velocity