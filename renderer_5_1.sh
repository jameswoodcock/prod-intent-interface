#!/bin/bash

pkill -f baseline_renderer
sleep .01
baseline_renderer -D JACK -o 64 -i 64 -c salford_5_1.xml -r 4240
