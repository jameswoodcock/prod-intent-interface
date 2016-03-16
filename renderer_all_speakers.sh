#!/bin/bash

pkill -f baseline_renderer
sleep .01
baseline_renderer -D JACK -o 64 -i 64 -c all_speakers.xml -r 4240
