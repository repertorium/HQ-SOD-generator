#!/Users/jaimegarcia/miniconda3/envs/reaper/bin/python
# -*- coding: utf-8 -*-
import pathlib
import subprocess
import ast
from reaper_python import *

def getAllTracks(proj=0):
  tracks = [RPR_GetTrack(proj,index) for index in range(RPR_CountTracks(proj))]
  
  return tracks

def getTrackName(track):
  _,_,_,track_name,_ = RPR_GetSetMediaTrackInfo_String(track, "P_NAME","",False)

  return track_name

def selectTrack(tracks,index):
  '''selecciona un track de la lista disponible, si index = -1, los deselecciona a todos'''
  if index >= 0:
    for n,track in enumerate(tracks):
      if n == index:
        RPR_SetMediaTrackInfo_Value(track,'I_SELECTED',1)
      else:
        RPR_SetMediaTrackInfo_Value(track,'I_SELECTED',0)
  else:
    for n,track in enumerate(tracks):
      RPR_SetMediaTrackInfo_Value(track,'I_SELECTED',0)

def splitInstruments(midi_filepath : pathlib.Path,
                      root_dir: pathlib.Path) -> list[pathlib.Path]:
  # construye comando para ejecutar el script `splitInstruments.py`
  command = [
              '/Users/jaimegarcia/Desktop/BBCSO/HQ-SOD-generator/Reaper/splitInstruments.py',
              '-m',midi_filepath,
              '-d',root_dir,
  ]
  # llama al script (devuelve la ruta a cada uno de los ficheros)
  command_result = subprocess.run(command,capture_output=True,text=True)
  stdout = command_result.stdout
  midi_filepaths = [pathlib.Path(filepath) for filepath in stdout.split(',')]

  return midi_filepaths

def insertInstruments(midi_filepaths: list[pathlib.Path],
                      tracks: list,
                      track_names: list):
  '''
  Inserta los ficheros de cada instrumento MIDI en el track correspondiente
  '''
  # deselecciona todos los tracks y ajusta la posicion
  # del cursor al principio del proyecto
  selectTrack(tracks,-1)
  RPR_SetEditCurPos(0, True, True)
  # itera por cada uno de los ficheros MIDI
  for midi_filepath in midi_filepaths:
    # obtiene el nombre del fichero (sin sufijo)
    midi_filename = midi_filepath.stem
    # itera por los nombres de los tracks y comprueba si hay match
    for n,track_name in enumerate(track_names):
      if track_name.split('MIDI_')[-1] != midi_filename:
        continue
      # si hay match, inserta el archivo midi en este track
      selectTrack(tracks,n)
      RPR_ShowConsoleMsg(f'Match between {midi_filename} and MIDI track {n+1}\n')
      RPR_ShowConsoleMsg(f'Inserting {str(midi_filepath)} at track {track_name}\n\n')
      RPR_InsertMedia(str(midi_filepath), 0)
      RPR_SetEditCurPos(0, True, True)

def getMidiTempoIntervals(midi_filepath:str) -> list[tuple[float,float]]:
  '''
  Obtiene los cambios de tempo del MIDI importado, solo hace falta evaluar
  uno de los instrumentos ya que todos siguen los mismos intervalos de tempo
  '''
  # construye el comando para ejecutar el script `getTempoChanges.py`
  command = [
              '/Users/jaimegarcia/Desktop/BBCSO/HQ-SOD-generator/Reaper/getTempoChanges.py',
              '-m',midi_filepath,
  ]
  command_result = subprocess.run(command,capture_output=True,text=True)
  stdout = command_result.stdout
  RPR_ShowConsoleMsg(f'Change times and tempo intervals:\n {stdout}\n')
  times_tempo_pairs = ast.literal_eval(stdout)
  
  return times_tempo_pairs

def setProjectTempoIntervals(midi_filepath: str):
  '''
  Ajusta intervalos de tempo en el proyecto en funcion del archivo midi
  importado
  '''
  times_tempo_pairs = getMidiTempoIntervals(midi_filepath)
  for change_time, tempo_value in times_tempo_pairs:
    RPR_SetTempoTimeSigMarker(0, -1, change_time, -1, -1, round(tempo_value), 0,0,False)

def deleteAllTempoMarkers():
  '''
  Elimina todos los marcadores de tempo del proyecto.

  Lo hace en orden descedente porque la lista que contiene los marcadores
  va modificando el orden de los mismos a medida que se eliminan, haciendo
  que la iteracion procese todos los items si se hace en orden ascendente. 
  '''
  num_markers = RPR_CountTempoTimeSigMarkers(0)
  RPR_ShowConsoleMsg(f'Number of tempo markers to be deleted: {num_markers}\n')
  for n in range(num_markers-1,-1,-1):
    RPR_ShowConsoleMsg(f'Deleting tempo marker {n}\n')
    RPR_DeleteTempoTimeSigMarker(0, n)

def deleteTrackMediaItems(track):
  '''
  Elimina todos los items multimedia de un track
  '''
  # obtiene los items de este track
  n_items = RPR_GetTrackNumMediaItems(track)
  media_items = [RPR_GetTrackMediaItem(track, index) for index in range(n_items)]
  # borra
  for item in media_items:
    RPR_DeleteTrackMediaItem(track, item)

def getNextFilepath() -> tuple[int,str]:
  '''
  Consulta al dispatcher el siguiente fichero midi a procesar
  '''
  command = [
              '/Users/jaimegarcia/Desktop/BBCSO/HQ-SOD-generator/Reaper/dispatcher.py',
              '--next'
            ]
  command_result = subprocess.run(command,capture_output=True,text=True)
  exit_code = command_result.returncode
  next_filepath = command_result.stdout

  return exit_code, next_filepath

def popFilepath() -> int:
  '''
  Pide al dispatcher que elimine el fichero de la lista
  '''
  command = [
              '/Users/jaimegarcia/Desktop/BBCSO/HQ-SOD-generator/Reaper/dispatcher.py',
              '--remove'
            ]
  command_result = subprocess.run(command,capture_output=True,text=True)

  return command_result.returncode

def main(root_dir: str, midi_filepath: str):
  # obtiene los nombres de los tracks del proyecto
  tracks = getAllTracks()
  track_names = [getTrackName(track) for track in tracks]
  RPR_ShowConsoleMsg(f'track names:{track_names}\n\n')
  # separa los instrumentos en archivos midi de forma temporal
  midi_filepaths = splitInstruments(midi_filepath,root_dir)
  # importa los ficheros de cada instrumento en su track correspondiente
  insertInstruments(midi_filepaths,tracks,track_names)
  # ajusta los marcadores de tempo
  setProjectTempoIntervals(midi_filepath)
  # ajusta la ventana de tiempo
  project_length = RPR_GetProjectLength(0)
  RPR_GetSet_LoopTimeRange2(0, True, False, 0, project_length, False)
  # selecciona los tracks de audio
  selectTrack(tracks,-1)
  RPR_ShowConsoleMsg('Selected tracks:\n')
  for n,(track,track_name) in enumerate(zip(tracks,track_names)):
    if track_name.startswith('AUDIO_'):
      RPR_SetMediaTrackInfo_Value(track,'I_SELECTED',1)
      RPR_ShowConsoleMsg(f'Audio track {n+1} - {track_name}\n')
  # ajusta el directorio de salida y renderiza
  render_output_directory = pathlib.Path(root_dir).parent / 'render'
  render_output_directory.mkdir(parents=True,exist_ok=True)
  RPR_GetSetProjectInfo_String(0, "RENDER_FILE", render_output_directory, True)
  RPR_Main_OnCommand(41824, 0)
  # elimina todos los intervalos de tempo, items multimedia, deselecciona tracks
  #  y elimina ventana de tiempo
  deleteAllTempoMarkers()
  for track in tracks:
    deleteTrackMediaItems(track)
  selectTrack(tracks,-1)
  RPR_GetSet_LoopTimeRange2(0, True, False, 0, 0, False)

if __name__ == '__main__':
  # directorio de salida de los ficheros midi de instrumentos
  root_dir = '/Users/jaimegarcia/Desktop/BBCSO/ReaScript/.temp'
  exit_code = 0
  while(exit_code == 0):
    # consulta el siguiente fichero a procesar
    exit_code, next_filepath = getNextFilepath()
    if exit_code != 0:
      break
    RPR_ShowConsoleMsg(f'Next MIDI filepath: {next_filepath}\n')
    # procesa el fichero
    main(root_dir,midi_filepath=next_filepath)
    # elimina el fichero de la lista
    exit_code = popFilepath()