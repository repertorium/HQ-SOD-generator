'''
This module provides useful tools when processing MIDI files
'''
import pretty_midi
import numpy as np
import matplotlib.pyplot as plt
from hashlib import sha256

def plotMIDI(midi_data: pretty_midi.PrettyMIDI) -> None:
    '''
    Represents the midi notes within a MIDI file as a heatmap,
    with colormap based on MIDI notes velocity values

    # Parameters:
    - midi_data: Midi data from a midi file modeled as a PrettyMidi object
    '''
    # number of instruments
    n_instrument = len(midi_data.instruments)
    fig,ax = plt.subplots(n_instrument,1, figsize=(10,8),squeeze=True,sharex='col')
    for n,instrument in enumerate(midi_data.instruments):
        # notes starting and ending times and pitches
        note_start_times = np.array([note.start for note in instrument.notes])
        if note_start_times[0] != 0:
            step = note_start_times[1] - note_start_times[0]
            note_start_times = np.hstack([np.arange(0,note_start_times[0],step),note_start_times])
        note_pitches = [note.pitch for note in instrument.notes]
        # pitch values are fixed -> [0-127]
        pitches = np.arange(min(note_pitches),max(note_pitches) +1,1,dtype=int)
        # initialize velocities matrix
        X, Y = np.meshgrid(note_start_times,pitches)
        velocity_matrix = np.zeros(X.shape,dtype=int)
        # fill-in velocities matrix by iterating over each note
        for note in instrument.notes:
            pitch_index = np.where(pitches == note.pitch)[0]
            time_index = np.where(note_start_times == note.start)[0]
            velocity_matrix[pitch_index,time_index] = note.velocity
        # set colormap
        im = ax[n].pcolormesh(X,Y,velocity_matrix,cmap='magma',vmin=0,vmax=127)

    fig.supxlabel('Duration (s)')
    fig.supylabel('MIDI Pitch')
    fig.suptitle('MIDI file plot')
    fig.subplots_adjust(bottom=0.1, top=0.9, left=0.1, right=0.8,wspace=0.02, hspace=0.02)
    # add colorbar to figure
    cb_ax = fig.add_axes([0.83, 0.1, 0.02, 0.8])
    cbar = fig.colorbar(im, cax=cb_ax,ticks=[*range(0,128,16)],label='MIDI Velocity')

def computeSeed(filename: str) -> int:
    '''
    Compute the seed for random processing of a MIDI file from its name.

    Seed is computed casting the SHA-256 hexadecimal output value integer
    and performing a modulo 2**32 operation

    # Parameter:
    - filename: The name of the MIDI file to be processed
    # Returns:
    - seed: The corresponding seed for this file
    '''
    hex_seed = sha256(filename.encode()).hexdigest()
    # convert from hexadecimal to decimal
    seed = int(hex_seed,base=16)

    return seed