#Author: Joe Redmon
#file_to_json.py

import md5, os
import simplejson
from display.models import MetaData, DataFile
from django.db import models

def displayfile(filestr):
    f = open(filestr, 'r')
    metadata = []
    data = []

    for line in f:
        line_array = line.split()
        if len(line_array) == 0:
            continue
        if line[0] == '#':
            metadata_name = line_array[0][1:]
            metadata_data = ' '.join(line_array[1:])
            metadata.append(dict(name=metadata_name, data=metadata_data))

        if line_array[0] == '#Columns':
            data.append(line_array[1:])
            break

    for line in f:
        if line[0] == '#': break
        data.append(line.split())

    return dict(metadata=metadata, data=data)

def displaystring(st):
    metadata = []
    data = []
    f = st.splitlines()
    i = 0
    for line in f:
        i+=1
        line_array = line.split()
        if len(line_array) == 0:
            continue
        if line[0] == '#':
            metadata_name = line_array[0][1:]
            metadata_data = ' '.join(line_array[1:])
            metadata.append(dict(name=metadata_name, data=metadata_data))

        if line_array[0] == '#Columns':
            data.append(line_array[1:])
            break

    for line in f[i:]:
        if line[0] == '#': break
        data.append(line.split())

    return dict(metadata=metadata, data=data)
