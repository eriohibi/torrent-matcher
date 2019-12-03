# This program takes a collection of torrent files and a list of directories,
#     and finds which torrents have matching local files.

import os

# Load from file a list of directories to check for files
directories = open('directories.txt', 'r').readlines()
directories = [s.strip() for s in directories]

# Traverse the given directories and record found files
print('Generating file listing...', end=' ')
files = []

for d in directories:
    for dir_name, subdir_list, file_list in os.walk(d):
        for f in file_list:
            files.append({
                'filename': f,
                'location': dir_name
            })

print('Done')
