# copy files from directory and replace names

import os
import shutil

# get all files from directory


def get_files(source):
    files = []
    for file in os.listdir(source):
        if file.endswith(".png"):
            files.append(file)

    return files


path = os.path.dirname(os.path.abspath(__file__))
files = get_files(path)

for index, file in enumerate(files):
    replace_number = str(index+1+180).zfill(3)
    shutil.copy(path + "\\" + file,
                path + "\\" + file.replace(file.split("_")[0], replace_number))
    if index == 60:
        break
