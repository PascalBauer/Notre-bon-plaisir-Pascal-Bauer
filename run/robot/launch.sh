#!/bin/bash

export LAUNCH_ROBOT00=false
export launch_robot00=false
export LAUNCH_ROBOT01=false
export LAUNCH_ROBOT02=false
export LAUNCH_ROBOT03=false
export LAUNCH_ROBOT04=false
export LAUNCH_ROBOT05=false
export LAUNCH_ROBOT06=false

for var in "$@"
do
    if [ "$var" = 00 ]; then
    	export LAUNCH_ROBOT00=true
    	bash ~/catkin_ws/run/robot/script_before_launch_for_robot.sh 00
    fi
    
    if [ "$var" = 01 ]; then
    	export LAUNCH_ROBOT01=true
		bash ~/catkin_ws/run/robot/script_before_launch_for_robot.sh 01
    fi
    
    if [ "$var" = 02 ]; then
    	export LAUNCH_ROBOT02=true
		bash ~/catkin_ws/run/robot/script_before_launch_for_robot.sh 02
    fi
    
    if [ "$var" = 03 ]; then
    	export LAUNCH_ROBOT03=true
		bash ~/catkin_ws/run/robot/script_before_launch_for_robot.sh 03
    fi
    
    if [ "$var" = 04 ]; then
    	export LAUNCH_ROBOT04=true
		bash ~/catkin_ws/run/robot/script_before_launch_for_robot.sh 04
    fi
    
    if [ "$var" = 05 ]; then
    	export LAUNCH_ROBOT05=true
		bash ~/catkin_ws/run/robot/script_before_launch_for_robot.sh 05
    fi
    
    if [ "$var" = 06 ]; then
    	export LAUNCH_ROBOT06=true
		bash ~/catkin_ws/run/robot/script_before_launch_for_robot.sh 06
    fi
done

#launch robot
roslaunch robot init_global.launch
