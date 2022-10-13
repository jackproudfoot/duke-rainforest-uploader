import datetime
from wsgiref import headers
from dateutil import parser
import pathlib
import json
from metadata.extract import extract_metadata
from tabulate import tabulate

def import_media(media_path, metadata_path = None, debug = False):
    media_dir = pathlib.Path(media_path)

    # Initialize metadata dir
    metadata_dir = media_dir.joinpath('metadata')
    if (metadata_path != None):
        metadata_dir = pathlib.Path(metadata_path).resolve()
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Get list of videos and images to import
    videos = sorted(media_dir.glob('*.MP4'))
    images = sorted(media_dir.glob('*.JPG'))

    # Extract runs from metadata
    runs = {}
    for video in videos:
        # Get path to metadata file
        video_metadata_file = metadata_dir.joinpath(video.name).with_suffix(video.suffix + '.json')

        # If metadata doesn't exist, extract it
        if (not video_metadata_file.exists()):
            extract_metadata(video, metadata_path=metadata_dir, debug=debug)

        # Load metadata from file
        with open(video_metadata_file, 'r') as f:
            video_metadata = json.load(f)
        
        # Get run
        run_id = video_metadata['session']['run_id']

        # Calculate video recording end time
        media_time = parser.parse(video_metadata['session']['media_date'])
        media_end_delta = datetime.timedelta(microseconds=video_metadata['frame'][-1]['time'])
        media_end = media_time + media_end_delta

        # Create new run if it doesn't exist
        if run_id not in runs.keys():
            start_time = parser.parse(video_metadata['session']['run_date'])

            runs[run_id] = {
                'run_id': run_id,
                'start': start_time,
                'end': media_end,
                'media': [video]
            }
        
        # Add video to media list
        runs[run_id]['media'].append(video)

        # Update ending time if video ends later
        if (media_end > runs[run_id]['end']):
            runs[run_id]['end'] = media_end
    
    # Sort the runs by time
    sorted_runs = sorted(runs.values(), key=lambda d: d['start'])

    unsorted_images = []

    # Add images to runs
    for image in images:
        # Get path to metadata file
        image_metadata_file = metadata_dir.joinpath(image.name).with_suffix(image.suffix + '.json')

        # If metadata doesn't exist, extract it
        if (not image_metadata_file.exists()):
            extract_metadata(image, metadata_path=metadata_dir, debug=debug)

        # Load metadata from file
        with open(image_metadata_file, 'r') as f:
            image_metadata = json.load(f)

        # Extract the time image was taken

        raw_datetime_parts = image_metadata['DateTime'].split(" ")
        raw_datetime_parts[0] = raw_datetime_parts[0].replace(":", "-")


        image_time = parser.parse(raw_datetime_parts[0] + 'T' + raw_datetime_parts[1] + image_metadata['OffsetTime'])

        # Add image to run
        image_sorted = False
        for run in sorted_runs:
            if (image_time >= run['start'] and image_time <= run['end']):
                run['media'].append(image)
                image_sorted = True
                break

        if not image_sorted:
            unsorted_images.append(image)
            
            if debug:
                print('\u001b[31mCould not automatically sort image: {} at time: {}\u001b[0m'.format(image.name, image_time))

    
    # Format tabular output

    runs_table = [
        [ run['run_id'], run['start'], run['end'], tabulate([
            [media_path.name] for media_path in run['media']
        ], tablefmt="plain")
        ]
        for run in sorted_runs
    ]

    colored_headers = ['\u001b[36m{}\u001b[0m'.format(header) for header in ['Run ID', 'Start Time', 'Approx. End Time', 'Media']]

    print(tabulate(runs_table, headers=colored_headers, tablefmt="simple_grid"))

    # Unsorted images
    if len(unsorted_images) > 0:
        colored_headers = ['\u001b[31m{}\u001b[0m'.format(header) for header in ['Unsorted Images (Not Imported)']]
        print(tabulate([[image] for image in unsorted_images], headers=colored_headers, tablefmt='simple_grid'))