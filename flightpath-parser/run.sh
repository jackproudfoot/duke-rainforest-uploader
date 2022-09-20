#!/bin/bash

docker run --name flightparser -v /Users/jack/Coursework/Drones/Raymond:/home/pdraw/raw --rm -i -t flightparser:latest bash
# vmeta-extract --json /home/pdraw/raw/vid.mp4