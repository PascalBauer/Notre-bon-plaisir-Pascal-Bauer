#!/bin/bash
robot=$1
#robot=$2

cd ~/catkin_make/run/mapping && make clean; make

user=$USER

#set time on odroid
ssh odroid@192.168.150.1$robot 'echo odroid|sudo -S service ntp stop; echo odroid|sudo -S ntpdate 192.168.150.1'


cd ~/catkin_ws/bin/ && ./mapping
