# This program takes a collection of torrent files and a list of directories,
#     and finds which torrents have matching local files.

import operator
import os
import sys
import torrent_parser as tp

import colorama
from colorama import Fore, Style

DEBUG = False
colorama.init()

# Load from file a list of directories to check for files
directories = open('directories.txt', 'r').readlines()
directories = [s.strip() for s in directories]

# Traverse the given directories and record found files
print('Generating file listing...')
files = []

for d in directories:
    for dir_name, subdir_list, file_list in os.walk(d):
        for f in file_list:
            files.append({
                'filename': f,
                'location': dir_name
            })

        print(f'{len(files)} files found', end='\r')

print(f'Done ({len(files)} files recorded)')

# Get from program arguments the directory of torrent files to check
if len(sys.argv) < 2:
    print('No arguments given')
    exit()

torrent_dir = sys.argv[1]
torrent_files = []

for dir_name, subdir_list, file_list in os.walk(torrent_dir):
    for f in file_list:
        if f[-8:] == '.torrent':
            torrent_files.append(dir_name + '/' + f)

print(f'{len(torrent_files)} torrent files discovered\n')

# Go through each torrent file and find matching local files.
#     Files are matched by looking at their full path in the torrent and seeing
#     if any local files also have that relative path.
#     This means that matching files won't be counted if they don't follow the
#     paths set in the torrent!
# TODO: Make this behaviour adjustable via a setting.
#       Also allow for checking against file size and hash if possible
i = 0
for t in torrent_files:
    i += 1
    torrent_info = tp.parse_torrent_file(t)

    # Check whether the torrent matches up with any local files
    matches = 0
    found_paths = {}  # Paths of matching files and # of times each is seen

    # Torrents list files under info/files, or sometimes just info/ if there
    #     is only a single file. In the latter case, the field of interest is
    #     "name" rather than "path"
    try:
        t_file_list = torrent_info['info']['files']
    except KeyError:
        try:
            t_file_list = [torrent_info['info']]
        except KeyError:
            # The torrent must not have any files?
            continue

    total = len(t_file_list)  # Total number of files that the torrent lists
    if total > 500:
        # Ignore torrents with a large amount of files
        # TODO: Fix this
        print(f'TOO MANY FILES ({total}): {t}')
        continue

    # Go through each file that the torrent lists and see if it exists in our
    #     already built local file list
    for f in t_file_list:
        matched = False

        for local_f in files:
            local_f_path = local_f['location'] + '/' + local_f['filename']
            torrent_f_path = '/'.join(f['path']) if 'path' in f else f['name']

            # Trailing ~ are replaced with an underscore
            #     (on Linux, using Tixati)
            # TODO: Check whether other OSes/clients do this too
            torrent_f_path = torrent_f_path.replace('~/', '_/')

            if torrent_f_path in local_f_path:
                matches += 1
                matched = True

                # Save the path of this file so that we can later determine
                #     the path to the torrent's files as a whole
                if local_f['location'] in found_paths:
                    found_paths[local_f['location']] += 1
                else:
                    found_paths[local_f['location']] = 1

                # We could break here, since the file has been found. But
                #     consider the situation where you have a collection of
                #     torrents uploaded by a single user. You may have
                #     "uploaded by X.txt" files in many places, and accepting
                #     the first one seen would result in bad path stats.

        if not matched and DEBUG:
            print(f'No match for {f}')

    # Here we find which local paths are the most common, because this can be
    #     used to determine where the torrent as a whole is saved
    found_paths_sorted = sorted(
        found_paths.items(),
        key=operator.itemgetter(1),
        reverse=True  # Paths with more hits appear first in the list
    )

    if len(found_paths_sorted) > 1:
        # First take the most common path. It might be something like
        #     "Movies/Avatar/Extras", while the torrent as a whole is saved to
        #     "Movies/Avatar". So what we do here is check the rest of the
        #     paths, and if any of them are a substring of this first path, we
        #     use that one instead. Another seen file in this example would be
        #     "Movies/Avatar/Avatar.mkv", which has the path
        #     "Movies/Avatar". So the resulting path would end up being this.
        local_path = found_paths_sorted[0][0]

        for path in found_paths_sorted[1:]:
            if path[0] in local_path:
                local_path = path[0]

    elif len(found_paths_sorted) == 1:
        local_path = found_paths_sorted[0][0]

    else:
        local_path = '?'

    # If every file in the torrent is matched with a local one, we have a
    #     complete torrent detected. However, this doesn't necessarily mean
    #     that the files are all in the correct tree structure! We only know
    #     that the paths all match up.
    # Anyway, print out some pretty results.
    fi = f'{str(i).rjust(5)}. '

    frmtd_torrent = t.split('/')[-1]
    frmtd_torrent = '' \
        .join([c if ord(c) < 128 else '_' for c in frmtd_torrent[:-8]])

    frmtd_torrent = '...' + frmtd_torrent[-77:] \
        if len(frmtd_torrent) > 80 \
        else frmtd_torrent.ljust(80)

    frmtd_torrent \
        = Style.DIM + Fore.WHITE \
        + frmtd_torrent \
        + Style.RESET_ALL

    frmtd_arrow = Fore.CYAN + '->' + Style.RESET_ALL
    frmtd_local = Fore.WHITE + local_path + Style.RESET_ALL

    if matches >= total:
        print(f'{fi}{frmtd_torrent} {frmtd_arrow} {frmtd_local}')

    elif matches > 0:
        frmted_matches = f'{Style.DIM}({matches}/{total})'
        print(f'{fi}{Fore.YELLOW}Partial match {frmted_matches} \
for {frmtd_torrent}')

    else:
        print(f'{fi}{Fore.RED}No match for {t}{Style.RESET_ALL}')
