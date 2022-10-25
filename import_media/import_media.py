import datetime
from shutil import copyfile
from dateutil import parser
import pathlib
import json
from metadata.extract import extract_metadata
from tabulate import tabulate

'''
Import media from an external sd card in standard directory format
'''
def import_media(media_path, harddrive_path, metadata_path = None, debug = False):
    media_dir = pathlib.Path(media_path)

    # Initialize metadata dir
    metadata_dir = media_dir.joinpath('metadata')
    if (metadata_path != None):
        metadata_dir = pathlib.Path(metadata_path).resolve()
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Get list of videos and images to import
    videos = sorted(media_dir.glob('*.MP4'))
    images = sorted(media_dir.glob('*.JPG'))

    # Media that was unable to be parsed
    unparsed_media = []

    # Extract runs from metadata
    runs = {}
    for video in videos:
        # Get path to metadata file
        video_metadata_file = metadata_dir.joinpath(video.name).with_suffix(video.suffix + '.json')

        # If metadata doesn't exist, extract it
        if (not video_metadata_file.exists()):
            try:
                extract_metadata(video, metadata_path=metadata_dir, debug=debug)
            except Exception:
                unparsed_media.append(video)
                continue

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
        
        else:
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

    # Organize runs by date

    harddrive_dir = pathlib.Path(harddrive_path)

    dateruns = {}

    # Organize imported runs into dict by start date
    for run in sorted_runs:
        datestring = run['start'].strftime('%m-%d-%y')

        if not datestring in dateruns.keys():
            dateruns[datestring] = []

        dateruns[datestring].append(run)

    # Scan for existing flights on those days
    for date in dateruns.keys():
        existing_flights = get_existing_flights(harddrive_dir.joinpath(date))

        dateruns[date] = dateruns[date] + existing_flights 

    
    # Sort flights by start time and import files
    for date, date_flights in dateruns.items():
        sorted_flights = sorted(date_flights, key=lambda d: d['start'] if isinstance(d['start'], datetime.datetime) else parser.parse(d['start']))

        # Do pass in reverse order to avoid overwriting... hopefully
        for index, flight in enumerate(sorted_flights[::-1]):
            flight_num = len(sorted_flights) - index

            # Existing flight
            if 'current_flight_num' in flight:
                current_flight_num = flight['current_flight_num']

                # New flight # doesn't match current flight #
                if flight_num != current_flight_num:
                    current_flight_dir = harddrive_dir.joinpath(date).joinpath("Flight {}".format(current_flight_num))

                    current_flight_dir.rename(current_flight_dir.parent.joinpath("Flight {}".format(flight_num)))
            # New flight
            else:
                new_flight_dir = harddrive_dir.joinpath(date).joinpath("Flight {}".format(flight_num))

                new_flight_dir.mkdir(parents=True)

                print('Flight {}'.format(flight_num))

                # Create flight metadata file
                with open(new_flight_dir.joinpath('metadata.json'), 'w') as f:
                    json.dump({k: str(flight[k]) for k in ('run_id', 'start', 'end')}, f)

                # Import videos and photos
                for media in flight['media']:
                    print('Importing {}'.format(media))
                    #copyfile(media, new_flight_dir.joinpath(media.name))

    
    # Import unsorted media
    for unsorted_image in unsorted_images:
        print(unsorted_image)


    # Import unparsed media
    for unparsed in unparsed_media:
        print(unparsed)

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

    # Media that failed to parse
    if  len(unparsed_media) > 0:
        colored_headers = ['\u001b[31m{}\u001b[0m'.format(header) for header in ['Media Failed to Parse (Not Imported)']]
        print(tabulate([[video] for video in unparsed_media], headers=colored_headers, tablefmt='simple_grid'))

    

'''
Scans the provided drone path and determines the next flight index to use
Drone day path must be in format */Drone Name/MM-DD-YY
'''
def get_existing_flights(drone_day_path):
    parent_dir = pathlib.Path(drone_day_path)

    # If parent directory doesn't exist, return empty array
    if not parent_dir.exists():
        return []

    # Get existing flight directories
    existing_flights = sorted(parent_dir.glob('Flight *'))

    flights = []

    # Load start time from general flight metadata file
    for flight_dir in existing_flights:
        metadata_filepath = flight_dir.joinpath('metadata.json')

        with open(metadata_filepath, 'r') as f:
            metadata = json.load(f)
            metadata['current_flight_num'] = flight_dir.name.split(' ')[1]
            flights.append(metadata)
    
    return flights