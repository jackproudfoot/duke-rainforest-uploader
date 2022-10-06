
import subprocess
import pathlib
import json

from PIL import Image, TiffImagePlugin, ExifTags

VIDEO_FORMATS = ['.mp4']
PHOTO_FORMATS = ['.jpg']

def extract_metadata(media_file, debug = False):
    filetype = pathlib.Path(media_file).suffix.lower()

    if (filetype in VIDEO_FORMATS):
        extract_video_metadata(media_file, debug)
    elif (filetype in PHOTO_FORMATS):
        extract_photo_metadata(media_file, debug)
    else:
        print('Error media format (%s) not supported.' % filetype)

def extract_photo_metadata(photo_file, debug = False):
    print('Extracting metadata from image ({})'.format(photo_file))

    # Open image using Pillow library
    image = Image.open(photo_file)

    exif = {}

    # Parse exif data and make it serializeable
    for k, v in image._getexif().items():
        if k in ExifTags.TAGS:
            if isinstance(v, TiffImagePlugin.IFDRational):
                v = float(v)
            elif isinstance(v, tuple):
                v = tuple(float(t) if isinstance(t, TiffImagePlugin.IFDRational) else t for t in v)
            elif isinstance(v, bytes):
                v = v.decode(errors="replace")
            exif[ExifTags.TAGS[k]] = v

    # Add proper gps tags and make values serializeable
    old_gps_info = exif['GPSInfo']
    exif['GPSInfo'] = {}

    for k, v in old_gps_info.items():
        if isinstance(v, TiffImagePlugin.IFDRational):
            v = float(v)
        elif isinstance(v, tuple):
            v = tuple(float(t) if isinstance(t, TiffImagePlugin.IFDRational) else t for t in v)
        elif isinstance(v, bytes):
            v = v.decode(errors="replace")
        exif['GPSInfo'][ExifTags.GPSTAGS.get(k, k)] = v

    image.close()

    print('Metadata extracted!')

    if debug:
        print(json.dumps(exif, indent=2))

    # Save image exif metadata to .json file
    metadata_file = pathlib.Path(photo_file).with_suffix(pathlib.Path(photo_file).suffix + '.json')
    with open(metadata_file, 'w') as f:
        json.dump(exif, f, indent=2)

'''
Run docker container containing vmeta-extract tool to extract frame metadata from videos
https://github.com/Parrot-Developers/libvideo-metadata
'''
def extract_video_metadata(video_file, debug = False):
    # Get relative path to script from current working directory
    script = pathlib.Path(__file__).parent.joinpath('extract.sh').relative_to(pathlib.Path.cwd())

    # Separate the path into the directory and file
    path = pathlib.PurePath(video_file)
    dir = path.parent.as_posix()
    vid = path.name

    print('Extracting metadata from video ({}) in ({})'.format(vid, dir))

    try:
        proc = subprocess.run(['sh', './{}'.format(script), dir, vid], stdout=subprocess.PIPE)

        if debug:
            print(proc.stdout.decode())

        print('Success!')

    except subprocess.CalledProcessError as err:
        print('Failed to extract frame metadata from {}: {}'.format(video_file, err))

    