from curses import meta
from distutils.log import debug
import flightpath.extract as flightpath_parser
import argparse
from pathlib import Path

def main(args):
    video_file = Path.cwd().joinpath(args.filename).resolve()

    flightpath_parser.extract_metadata(video_file, debug=True)

    metadata_file = video_file.with_suffix(video_file.suffix + '.json')

    metadata = flightpath_parser.sample_frames(metadata_file)

    print(metadata)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Rainforest Xprize Uploader')

    arg_parser.add_argument('filename')

    args = arg_parser.parse_args()

    main(args)

   