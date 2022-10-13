
import subprocess
import pathlib
import json

from PIL import Image, TiffImagePlugin, ExifTags

def extract_metadata(media_file, metadata_path = None, debug = False):
    filetype = pathlib.Path(media_file).suffix.lower()

    if (filetype == '.mp4'):
        extract_video_metadata(media_file, metadata_path, debug)
    elif (filetype == '.jpg'):
        extract_photo_metadata(media_file, metadata_path, debug)
    else:
        print('Error media format (%s) not supported.' % filetype)

def extract_photo_metadata(photo_file, metadata_path = None, debug = False):
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


    # Set metadata path
    photo_path = pathlib.Path(photo_file)
    metadata_dir = photo_path.parent

    if (metadata_path != None):
        metadata_dir = pathlib.Path(metadata_path).resolve()
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Save image exif metadata to .json file
    metadata_file = metadata_dir.joinpath(photo_path.name).with_suffix(photo_path.suffix + '.json')
    with open(metadata_file, 'w') as f:
        json.dump(exif, f, indent=2)

'''
Run docker container containing vmeta-extract tool to extract frame metadata from videos
https://github.com/Parrot-Developers/libvideo-metadata
'''
def extract_video_metadata(video_file, metadata_path = None, debug = False):
    # Get relative path to script from current working directory
    script = pathlib.Path(__file__).parent.joinpath('extract.sh').relative_to(pathlib.Path.cwd())

    # Separate the path into the directory and file
    video_path = pathlib.PurePath(video_file)
    dir = video_path.parent.as_posix()
    vid = video_path.name

    print('Extracting metadata from video ({}) in ({})'.format(vid, dir))

    try:
        proc = subprocess.run(['sh', './{}'.format(script), dir, vid], stdout=subprocess.PIPE)

        if debug:
            print(proc.stdout.decode())

        

    except subprocess.CalledProcessError as err:
        print('Failed to extract frame metadata from {}: {}'.format(video_file, err))
        return
    
    # Move metadata file if metadata path set
    if (metadata_path != None):
        metadata_dir = pathlib.Path(metadata_path).resolve()
        metadata_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = pathlib.Path(video_path.with_suffix(video_path.suffix + '.json'))
        metadata_file.rename(metadata_dir.joinpath(metadata_file.name))

    print('Success!')

    