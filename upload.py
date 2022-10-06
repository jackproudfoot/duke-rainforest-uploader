from metadata.extract import extract_metadata
from metadata.util import sample_frames
import argparse
from pathlib import Path

def main(args):
    video_file = Path.cwd().joinpath(args.filename).resolve()

    extract_metadata(video_file, debug=True)

    #metadata_file = video_file.with_suffix(video_file.suffix + '.json')

    #metadata = flightpath_parser.sample_frames(metadata_file)

    #print(metadata)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Rainforest Xprize Uploader')

    arg_parser.add_argument('filename')

    args = arg_parser.parse_args()

    main(args)

   