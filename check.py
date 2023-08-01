import requests
import re
import regex
import tarfile
import subprocess
import getpass
import shutil
import os
import fileinput
import sys
from datetime import datetime
from tqdm import tqdm

intellij_url = "https://data.services.jetbrains.com/products?code=IIC&release.type=release"
desktop_file = "/usr/share/applications/intellij.desktop"

def main(): 

    print("Verifying local build...")
    localBuild = getLocalBuild()
    print(f"Local build: {localBuild}")
    print(f"Searchiing last version in {intellij_url}")
    response = requests.get(intellij_url)

    if response.status_code == 200:
        data = response.json()

        dwl_link = data[0]["releases"][0]["downloads"]["linux"]["link"]
        version = data[0]["releases"][0]["version"]
        build = data[0]["releases"][0]["build"]

        print("Remote version:", version)
        print("Remote build:", build)


        if comparar_versiones(build, localBuild) == 1:
            print(f"Remote build ({build}) is greater than local build ({localBuild})")
            print(f"Downloading new version from {dwl_link}...")
            localDwlfile = "/tmp/intellij-" + version + ".tar.gz"
            bajarArchivo(dwl_link, localDwlfile)
            dec_dir = decompress(localDwlfile)
            dec_dir = "/tmp/" + dec_dir
            print(f"Decompress dir: {dec_dir}")
            password = getpass.getpass("[sudo] password: ")
            if moveFile(dec_dir, "/opt/", password) == 0:
                oldDirName = "idea-IC-" + localBuild
                newDirName = dec_dir.split("/")[2]
                changeAppFile(oldDirName, newDirName, desktop_file, password)
        else:
            print("Local version is the same as last remote version.")
    else:
        print("Request error:", response.status_code)

def getLocalBuild():
    with open(desktop_file, 'r') as file:
        for linea in file:
            if "Exec" in linea:
                resultado = re.search(r"/idea-IC-(\d+\.\d+\.\d+)\b", linea)
                return resultado.group(1)

def bajarArchivo(dwl_link, tmp_file):
    dwl_response = requests.get(dwl_link, stream=True)
    total_size = int(dwl_response.headers.get('content-length', 0))
    progress_bar = tqdm(total=total_size, unit='B', unit_scale=True)

    if dwl_response.status_code == 200:
        # Guardar el contenido de la respuesta en un archivo
        with open(tmp_file, 'wb') as file:
            for datos in dwl_response.iter_content(1024):
                file.write(datos)
                progress_bar.update(len(datos))
        progress_bar.close()
        print(f"Download complete. ({dwl_link}) to ({tmp_file})")
        return 0
    else:
        print("Error downloading file:", dwl_response.status_code)
        return 1

def decompress(tmp_file):
    print(f"Init extracting file ({tmp_file}) to (/tmp/)...")
    with tarfile.open(tmp_file, 'r:gz') as archivo_tar:
        nombres = archivo_tar.getnames()
        directorio_principal = nombres[0] if nombres else None
        # Extraer todos los archivos del archivo comprimido
        archivo_tar.extractall("/tmp/")
    print('Extract OK', nombres[0])
    fecha_actual = datetime.now()
    timestamp = fecha_actual.timestamp()
    os.utime("/tmp/" + nombres[0], (timestamp, timestamp))
    return directorio_principal

def comparar_versiones(version1, version2):
    comp1 = list(map(int, version1.split('.')))
    comp2 = list(map(int, version2.split('.')))

    # Comparar los componentes en orden
    for c1, c2 in zip(comp1, comp2):
        if c1 > c2:
            return 1
        elif c1 < c2:
            return -1

    if len(comp1) > len(comp2):
        return 1
    elif len(comp1) < len(comp2):
        return -1
    else:
        return 0


def moveFile(originPath, destinationPath, password):
    res_mov_sudo = subprocess.run(['sudo', '-S', 'rsync', '-a', originPath, destinationPath], input=password, capture_output=True, text=True)
    if res_mov_sudo.returncode == 0:
        print("Directory moved.")
        return 0
    else:
        print("Error moving directory.")
        print(res_mov_sudo)
        return 1

def changeAppFile(oldName, newName, file, password):
    print(f"Replacing '{oldName}' by '{newName}' in file {file}")
    comando = eval(f'f"sed -i s/{oldName}/{newName}/g {file}"')
    comando_sudo = ['sudo', '-S'] + comando.split()
    subprocess.run(['sudo', '-S', 'cp', file, file + str(datetime.now().timestamp()) + ".bak"], input=password, capture_output=True, text=True)
    res_change_sudo = subprocess.run(comando_sudo, input=password, capture_output=True, text=True)
    if res_change_sudo.returncode == 0:
        print("File modification OK.")
        return 0
    else:
        print("Error file modification.")
        print(res_change_sudo)
        return 1

    print(comando_sudo)
    
main()
