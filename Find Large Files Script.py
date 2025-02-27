# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 15:51:07 2025

@author: sergi
"""

import os
from pathlib import Path
import pandas as pd
import sqlite3
import argparse

import logging
logging.basicConfig(filename="errors_Largest_Files_Script.log", level=logging.WARNING, 
                    format="%(asctime)s - %(levelname)s - %(message)s")


def findLargestFile(path):
    data = {}
    for root, _, files in os.walk(path):
        for archivo in files:
            relativePath = Path(root) / archivo
            
            try:
                if not relativePath.exists():
                    raise FileNotFoundError(f"Archivo no encontrado: {relativePath}")
                else:
                    tamaño = relativePath.stat().st_size
                    data[str(relativePath)] = tamaño
                    
            except FileNotFoundError as e:
                logging.warning(e)  # Guarda el error en errores.log
            except PermissionError:
                logging.warning(f"Permiso denegado: {relativePath}")  # Evita que el programa se detenga
            
    print(f'{len(data)} files where found in this path.')
    
    if not data:
        return pd.Series(dtype="float64")  # Evita error si no hay archivos
    
    serie = pd.Series(data).sort_values(ascending=False)
    serie = serie.apply(convertirPesos)
    return serie


def convertirPesos(peso):
    if peso < 1000:
        return f'{peso} B'
    elif peso < 1000000:
        return f'{round(peso/1000, 2)} KB'
    else:
        return f'{round(peso/1000000, 2)} MB'
    
    
def find_file_type(path, file_type): # (.mp4, .mp3, .jpeg, .html)
    datos = {}
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    df = findLargestFile(path).reset_index()                        # Convierte la serie en un DataFrame.
    df.columns = ["path", "size"]                                   # Asigna nombres a las columnas.
    df.to_sql("files", conn, if_exists="replace", index=False)      # Convierte el DataFrame en una tabla SQLite.
    
    query = f'SELECT * FROM files WHERE path LIKE "%{file_type}"'
    cursor.execute(query)
    
    for i in cursor.fetchall():
        datos[i[0]] = i[1]
    print(f'Of which {len(datos)} are {file_type} files.)\n')

    conn.close()
    
    return pd.Series(datos, dtype=object)


def main():
    parser = argparse.ArgumentParser('''El siguiente script organiza los archivos dado un path. Adicionalmente se puede pasar por parámetro la extensión de los archivos que se quieren buscar y la cantidad de estos en el resultado''')
                                     
    parser.add_argument('path', help='Ruta de la ubicación o directorio que contiene los archivos')
    parser.add_argument('--extension', help='Extensión de los archivos a buscar', default='')
    parser.add_argument('--top', type=int, help='Cantidad de archivos en el resultado', default=0)
    params = parser.parse_args()
    
    path, file_type, top = params.path, params.extension, params.top   #Se guardan los params en variables.
    
    if top != 0:
        print(f'Top {top} most heavy files (Series format):\n')
        answer = find_file_type(path, file_type).head(top)
    else:
        print('Your files organiced by size (Series format):\n')
        answer = find_file_type(path, file_type)
    print(answer)
    return answer


__name__
if __name__ == '__main__':
    main()