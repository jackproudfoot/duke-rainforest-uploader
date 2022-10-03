from math import floor, trunc
import subprocess
import pathlib
import json

'''
Run docker container containing vmeta-extract tool to extract frame metadata from videos
https://github.com/Parrot-Developers/libvideo-metadata
'''
def extract_metadata(video_file, debug = False):
    # Get relative path to script from current working directory
    script = pathlib.Path(__file__).parent.joinpath('extract.sh').relative_to(pathlib.Path.cwd())

    # Separate the path into the directory and file
    path = pathlib.PurePath(video_file)
    dir = path.parent
    vid = path.name

    print('Extracting metadata from video ({}) in ({})'.format(vid, dir))

    try:
        proc = subprocess.run(['sh', './{}'.format(script), dir, vid], stdout=subprocess.PIPE)

        if debug:
            print(proc.stdout.decode())

        print('Success!')

    except subprocess.CalledProcessError as err:
        print('Failed to extract frame metadata from {}: {}'.format(video_file, err))

'''
Sample the frame data in the metadata file at specified rate
'''
def sample_frames(metadata_file, sample_rate = 0.01):
    # Open metadata file and parse json
    f = open(metadata_file)
    data = json.load(f)

    # Get list of frames
    frames = data['frame']

    # Determine sampling jump, with minimum of 15 samples
    max_jump = trunc(len(frames) / 15)
    sampling_jump = min(trunc(sample_rate * 10000), max_jump)

    # Sample frame data
    samples = frames[::sampling_jump]

    return samples
    