#!/Users/jaimegarcia/miniconda3/envs/reaper/bin/python
'''
This script provide a CLI to scan the target directory for midi files,
create a json list file and implement a query mechanism that returns the
next file in the list to be processed.

Once processed, file should be deleted from the list file through this same script.
'''
import pathlib
import argparse
import json
import sys

def scan(dir:pathlib.Path,
         json_filepath:pathlib.Path) -> None:
    '''
    Scan target directory for midi file, output a json file with all midi file paths
    in the same directory this script is located
    '''
    data = {}
    filepaths = [str(file.resolve()) for file in dir.glob('*') if file.suffix in ['.mid','.MID']]
    filepaths.sort()
    data['filepaths'] = filepaths

    with open(json_filepath,'w') as f:
        json.dump(data,f,indent=4)

def getNext(json_filepath:pathlib.Path) -> str:
    '''
    Get next file path from the json list
    '''
    with open(json_filepath,'r') as f:
        data = json.load(f)
    
    return data['filepaths'].pop(0)

def removePath(json_filepath:pathlib.Path) -> None:
    '''
    Modifies json list file so the first path is removed from the list
    '''
    with open(json_filepath,'r') as f:
        data = json.load(f)
    
    data['filepaths'].pop(0)

    with open(json_filepath,'w') as f:
        json.dump(data,f,indent=4)

if __name__ == '__main__':
    # default output path and json file
    output_dir = pathlib.Path(__file__).resolve().parent
    output_json_filepath = output_dir / 'scanned_files.json'
    # CLI
    parser = argparse.ArgumentParser(description='''
                Provides a CLI to scan the target directory for midi files,
                create a json list file and implement a query mechanism that returns the
                next file in the list to be processed.

                Once processed, file should be deleted from the list file through
                this same program
                ''')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d','--directory',type=str,help='The directory to be scanned for MIDI files')
    group.add_argument('-n','--next',action='store_true',help='Get next file path in the list')
    group.add_argument('-r','--remove',action='store_true',help='Delete the next file path in the list (like `pop(0)` list method)')

    args = parser.parse_args()
    if args.directory:
        print('Scanning midi files within directory...')
        try:
            scan(dir=pathlib.Path(args.directory),json_filepath=output_json_filepath)
            print('Midi files succesfully scanned')
            print(f'JSON list file located at: {str(output_json_filepath)}')
            exit_code = 0
        except:
            sys.stderr.write('Something went wrong when trying to scan directory')
            exit_code = 1
        
    elif args.next:
        try:
            next_filepath = getNext(output_json_filepath)
            print(next_filepath)
            exit_code = 0
        except:
            exit_code = 1
            sys.stderr.write('Something went wrong when trying to read json list file')
    elif args.remove:
        print('Removing first path from the list...')
        try:
            removePath(json_filepath=output_json_filepath)
            print('Path succesfully removed')
            exit_code = 0
        except:
            sys.stderr.write('Either there are no file paths left to remove or json list does not exist')
            exit_code = 1
    
    sys.exit(exit_code)