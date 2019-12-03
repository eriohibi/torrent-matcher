# This program takes a collection of torrent files and a list of directories,
#     and finds which torrents have matching local files.

import os
import sys
import torrent_parser as tp

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

# Get from program arguments the torrent file to check
# TODO: Support a collection of torrent files
if len(sys.argv) < 2:
    print('No arguments given')
    exit()

torrent_file = sys.argv[1]
torrent_info = tp.parse_torrent_file(torrent_file)

# Check whether the torrent matches up with any local files
# TODO: Check whether path matches as well, not just filename.
#       And perhaps also file size and/or hash if possible
matches = 0
total = len(torrent_info['info']['files'])

for f in torrent_info['info']['files']:
    if f['path'][-1] in [x['filename'] for x in files]:
        matches += 1

print(f'Matches: {matches}/{total}')

# If every file in the torrent is matched with a local one, we have a complete
#     torrent detected
