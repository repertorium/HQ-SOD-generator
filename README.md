# HQ-SOD-generator

This software prepare and generate High Quality sounds to train AI-based music instrument source separation approaches based on the Symbolic Orchestral Database (SOD), which can be downloaded here: https://qsdfo.github.io/LOP/database.html

The steps to obtain the HQ signals are enumerated below

1.- Fixing the instrument information
Most of the MIDI files do not follow the General MIDI (GM) standard and the track names use many different names to refer to the same instrument. In the SOD dataset, every piece has a csv file with the instrument of some tracks, but they do not include all the tracks so they're not enough to fix the MIDIs. Therefore, we've handcrafted a dictionary to map all the different names to the GM names. 

2.- Generating diverse and representative conditions
The process involves random selection of time intervals within an adjustable range, random tempo assignment based on a normal distribution with adjustable parameters, random allocation of dynamics to these time intervals (with no adjacent intervals having the same dynamics), mapping dynamics to velocity ranges, and assigning random velocity values within these ranges to notes in each instrument's time interval. Additionally, there may be random progressive changes in dynamics between adjacent intervals, resulting in crescendos or diminuendos, with velocity values adjusted accordingly. This approach aims to create more natural and humanized musical sequences.

3.- Synthesis using HQ-soundfonts
To obtain the audio signals from the generated MIDI/musicXML scores, we used the Spitfire Audio synthesizer using the high-quality BBC symphony orchestra proffesional and the Albion one soundfonts. In order to automatize the synthesis routine, the synthetizer has been integrated into a Digital Audio Workstation (DAW) as a VST plugin and a software gateway has been implemented in order to automatically assign each instrument with each corresponding track. 
