#!/bin/bash

while true; do
    ffmpeg -i /dev/video0 -f mpegts -listen 1 tcp://localhost:8554
    sleep 1
done