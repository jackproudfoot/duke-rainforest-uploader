
import argparse
from datetime import datetime, timedelta
from glob import glob
from GPSPhoto import gpsphoto
from os import path
import requests


API_BASE_URL = 'http://localhost:8000'



def main():
    parser = argparse.ArgumentParser(description='Photo uploader arguments.')
    parser.add_argument('--drone_id', type=str, help='Drone vehicle ID', required=True)
    parser.add_argument('--photo_dir', type=str, help='Directory of photos', required=True)
    parser.add_argument('-r', '--recursive', action='store_true')
    args = parser.parse_args()
    drone_id = args.drone_id
    photo_dir = args.photo_dir
    recursive = args.recursive

    if not path.isdir(photo_dir):
        print('That directory does not exist.')
        return

    # TODO: this isn't working as expected...
    photo_paths = glob(path.join(photo_dir, '**', '*.jpg'), recursive=True)

    print(len(photo_paths))
        
    flight_res = requests.post(f'{API_BASE_URL}/drone/create_flight/', {
        'drone_id': drone_id,
        'pilot_name': 'Casey Slaught'
    })

    if flight_res.status_code != 201:
        print('Failed to create drone flight.')
        print(flight_res.json())
        return

    flight_uid = flight_res.json()['flight_uid']

    for p in photo_paths:
        print(p)

        with open(p, 'rb') as f:

            exif_data = gpsphoto.getGPSData(p)
            obs_res = requests.post(f'{API_BASE_URL}/drone/create_observation/', data={
                'flight_uid': flight_uid,
                'latitude': round(exif_data['Latitude'], 5),
                'longitude': round(exif_data['Longitude'], 5),
                'altitude': int(exif_data['Altitude'])
            }, files={
                'photo': open(p, 'rb')
            })

            if obs_res.status_code != 201:
                print('Failed to create drone observation.')
                print(obs_res.json())
                return


if __name__ == '__main__':
    main()

