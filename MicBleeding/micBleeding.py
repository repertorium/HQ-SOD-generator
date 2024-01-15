#! /Users/jaimegarcia/miniconda3/envs/head/bin/python
'''
This module simulates the audio bleeding phenomenon for high-quality
audio files obtained using the Spitfire synthesizer.

This effect is achieved by filtering the mentioned audio files with the
RIR estimation in each one of the microphone spots when the sound source is
located in one of these points.

The RIR files are stored inside the ./npy directory. Each RIR has the same
number of columns as microphone spots in the recording layout, samplerate is
44100 Hz.

Convolved sources are sum, so the bleeding is simulated for each one of the
microphone signals, that is, each column of the output array.
'''
import pathlib
import numpy as np
import soundfile as sf
from tqdm import tqdm
from scipy.signal import oaconvolve

# path to the RIR directory
RIR_directory = (pathlib.Path(__file__).parent / 'npy').resolve()
RIR_sr = 44100
# order of the columns for each one of the RIRs matrices
rir_mapping = ('Violin_1',
               'Violin_2',
               'Viola',
               'Cello',
               'Bass',
               'Flute',
               'Oboe',
               'Clarinet',
               'Bassoon',
               'Horn',
               'Trumpet',
               'Trombone',
               'Tuba',
               'Timpani',
               'untunedpercussion',
               'Harp',
               'Main_L',
               'Main_C')
# instruments contained in the SOD dataset, grouped by families
dataset_instruments = {
    'strings':['Bass','Cello','Viola','Violin_1','Violin_2'],
    'woodwinds':['coranglais','Clarinet','Piccolo','Bassoon','Oboe','Flute'],
    'brass':['Tuba','Trombone','Trumpet','Horn'],
    'percussion':['Vibraphone','Marimba','Celeste','tubularbells','Glockenspiel','Xylophone','Harp','untunedpercussion','Timpani']
}

class TooManyInstrumentsException(Exception):
    '''
    Raise this exception if the number of instruments played for a performance
    is greater than the number of available RIR
    '''
    pass

def getFilepaths(directory:pathlib.Path,
                      suffix:str) -> list[pathlib.Path]:
    '''
    Get the file paths of all the files with the specified suffix
    inside a directory
    '''
    filepaths = [file for file in directory.glob(f'*{suffix}')]
    return filepaths

def loadRIR(RIR_filepath: pathlib.Path) -> np.ndarray:
    '''
    Load the numpy array stored in the specified filepath
    '''
    with open(RIR_filepath,'rb') as f:
        RIR = np.load(f)
    
    return RIR

def splitByRIRAvailability(audio_filepaths: list[pathlib.Path],
                           RIR_filenames: list[str]) -> tuple[list[pathlib.Path],list[pathlib.Path]]:
    '''
    Returns two lists, one containing audio file paths of the instruments that have an
    available RIR and other list with audio file paths that don't have any available RIR
    '''
    # split instrument audio files dependening on the rir availability
    audiofiles_with_RIR = []
    audiofiles_without_RIR = []
    for audio_filepath in audio_filepaths:
        if audio_filepath.stem in RIR_filenames:
            audiofiles_with_RIR.append(audio_filepath)
        else:
            audiofiles_without_RIR.append(audio_filepath)
    
    return audiofiles_with_RIR, audiofiles_without_RIR

def filter(x:np.ndarray,
           RIR: np.ndarray) -> np.ndarray:
    '''
    Convolves the input audio signal with every column of the RIR.
    Since x is expected to be much longer than RIR, overlap-add convolution
    is preferred.
    '''
    len_x = len(x)
    len_RIR,columns = RIR.shape
    N = len_x + len_RIR - 1
    y = np.zeros([N,columns])
    for c in range(columns):
        y[:,c] = oaconvolve(x,RIR[:,c])
    
    return y

def instrumentsWithAvailableRIRProcessing(audiofiles_with_RIR: list[pathlib.Path],
                                          RIR_filepaths: list[pathlib.Path],
                                          RIR_filenames: list[str]) -> np.ndarray:
    '''
    Processes the audio files that have an available RIR associated.
    Used RIRs are removed from the `RIR_filepaths` list.
    '''
    y = None
    for n,audiofile_with_RIR in tqdm(enumerate(audiofiles_with_RIR),
                                     total=len(audiofiles_with_RIR),
                                     desc='Processing instruments with an available RIR'):
        print(f'\nInstrument: {audiofile_with_RIR.stem}')
        x,sr = sf.read(audiofile_with_RIR)
        if sr != RIR_sr:
            raise ValueError(f'Expected a samplerate of {RIR_sr} Hz. Got {sr} Hz')
        # get the RIR for this instrument
        RIR_index = RIR_filenames.index(audiofile_with_RIR.stem)
        RIR = loadRIR(RIR_filepaths[RIR_index])
        print(f'Loaded {RIR_filepaths[RIR_index].name}')
        if n == 0:
            y = filter(x,RIR)
        y += filter(x,RIR)
        RIR_filepaths.pop(RIR_index)
        RIR_filenames.pop(RIR_index)
    
    return y

def findFamily(instrument_name: str,
               dataset_instruments: dict = dataset_instruments) -> str | None:
    '''
    For an input instrument name, get its instrument family
    '''
    for family, instruments in dataset_instruments.items():
        if instrument_name in instruments:
            return family
    return None

def selectNonAssociatedRIR(instrument_name: str,
                           RIR_filenames: list[str]) -> int:
    '''
    Returns the index of a RIR for an instrument that doesn't
    have an available RIR
    '''
    family = findFamily(instrument_name)
    if family:
        family_instruments = dataset_instruments[family]
        # find the available RIRs for all the family instruments
        family_RIR_indices = [RIR_filenames.index(family_instrument) for family_instrument in family_instruments if family_instrument in RIR_filenames]
        # select the first available RIR if possible
        if family_RIR_indices:
            RIR_index = family_RIR_indices[0]
        # if there are no RIRs available for the same instrument family, select the first available one
        else:
            RIR_index = 0
    
    return RIR_index

def instrumentsWithoutAvailableRIRProcessing(audiofiles_without_RIR: list[pathlib.Path],
                                          RIR_filepaths: list[pathlib.Path],
                                          RIR_filenames: list[str]) -> np.ndarray:
    
    for n,audiofile_without_RIR in tqdm(enumerate(audiofiles_without_RIR),
                                    total=len(audiofiles_without_RIR),
                                    desc='Processing instruments without an available RIR'):
        print(f'\nInstrument: {audiofile_without_RIR.stem}')
        x,sr = sf.read(audiofile_without_RIR)
        if sr != RIR_sr:
            raise ValueError(f'Expected a samplerate of {RIR_sr} Hz. Got {sr} Hz')
        # get a RIR for this instrument
        RIR_index = selectNonAssociatedRIR(audiofile_without_RIR.stem,RIR_filenames)
        RIR = loadRIR(RIR_filepaths[RIR_index])
        print(f'selected RIR for {audiofile_without_RIR.stem}: {RIR_filepaths[RIR_index].name}')
        if n == 0:
            y = filter(x,RIR)
        y += filter(x,RIR)
        RIR_filepaths.pop(RIR_index)
        RIR_filenames.pop(RIR_index)
    
    return y

def micBleeding(audio_directory: pathlib.Path,
                output_directory: pathlib.Path,
                audiofile_suffix: str = '.flac',
                RIR_directory: pathlib.Path = RIR_directory):
    # get the instrument audio file paths and names
    audio_filepaths = getFilepaths(audio_directory,suffix=audiofile_suffix)
    # get the RIR file paths and file names
    RIR_filepaths = getFilepaths(RIR_directory,suffix='.npy')
    RIR_filenames = list(map(lambda file: file.stem, RIR_filepaths))
    # stop execution if there are more instruments than available RIRs
    if len(audio_filepaths) > len(RIR_filepaths):
        raise TooManyInstrumentsException()
    audiofiles_with_RIR, audiofiles_without_RIR = splitByRIRAvailability(audio_filepaths,RIR_filenames)
    # firstly, process the audio files with an available RIR
    y = instrumentsWithAvailableRIRProcessing(audiofiles_with_RIR,RIR_filepaths,RIR_filenames)
    # process the audio files without an available RIR
    y = y + instrumentsWithoutAvailableRIRProcessing(audiofiles_without_RIR,RIR_filepaths,RIR_filenames)
    # normalize signals
    len_y,channels = y.shape
    Amax = max(np.max(abs(y),axis=0))
    print(f'Amax = {Amax}')
    if Amax > 1:
        y = y/Amax * 0.9
    # save to disk memory
    output_directory.mkdir(parents=True,exist_ok=True)
    for n in range(channels):
        sf.write(output_directory / f'channel_{n}.flac',y[:,n],44100)

if __name__ == '__main__':
    
    audio_directory = pathlib.Path('/Users/jaimegarcia/Downloads/Close Mic/test')
    output_directory = pathlib.Path('./test_results').resolve()
    micBleeding(audio_directory,output_directory)