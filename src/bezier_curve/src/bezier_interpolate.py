#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import rospy
from scenario_msgs.msg import Scenario as ScenarioMsg
from scenario_msgs.msg import Path as PathMsg
from geometry_msgs.msg import Pose as PoseMsg
from geometry_msgs.msg import Point as PointMsg
from std_msgs.msg import Float64 as Float64Msg

# consts
DEFAULT_BEZIER_CURVE_STEP = .05
path = PathMsg()
step = 0
stepInMeter = 0

def scenarioCallback(data):
    # to execute only choregraphic scenario
    path.uid = data.uid
    path.path.poses = []
    path.path.header = data.bezier_paths.header
    distance = 0
    duration = 0
    rospy.loginfo("New scenario")
    
    for media in data.medias.medias:
        duration += media.duration
    
    for curve in data.bezier_paths.curves:
        distance += getBezierCurveLength(curve)
        i = 0
        step = 1.0 * stepInMeter / getBezierCurveLength(curve)
        while i <= 1 :  
            pose = PoseMsg()
            
            if data.type == "choregraphic":
                pose.position = getBezierCurveResult(i, curve)
                theta = getBezierCurveTangentResult(i, curve)
                pose.orientation.z = math.sin(theta / 2)
                pose.orientation.w = math.cos(theta / 2)
                rospy.loginfo("Pose %f/100: %f | %f",i*100,pose.position.x,pose.position.y)
                i += step
            elif data.type == "travel":
                pose.position.x = curve.anchor_1.x
                pose.position.y = curve.anchor_1.y
                theta = curve.anchor_1.z
                pose.orientation.z = math.sin(theta / 2)
                pose.orientation.w = math.cos(theta / 2)
                
                i += 2
                
            path.path.poses.append(pose)
            
            
    speed = Float64Msg()
    speed.data = (distance / duration) if duration > 0 else 0.1
    speedPublisher.publish(speed)
    pathPublisher.publish(path)


""" method to calculate the value of a point of a bezier curve 

:param u: position of the curve which we want to calculate, from 0 to 1
:type u: float
:param bezierCurve: coords of the start point, end point and tangent for each of them for the curve
:type bezierCurve: bezier_curve.msg.BezierCurve
:returns: result point
:rtype: geometry_msgs.msg.Point
"""
def getBezierCurveResult(u, bezierCurve):
    result = PointMsg()
    result.x = pow(u, 3) * (bezierCurve.anchor_2.x + 3 * (bezierCurve.control_1.x - bezierCurve.control_2.x) - bezierCurve.anchor_1.x) \
               + 3 * pow(u, 2) * (bezierCurve.anchor_1.x - 2 * bezierCurve.control_1.x + bezierCurve.control_2.x) \
               + 3 * u * (bezierCurve.control_1.x - bezierCurve.anchor_1.x) + bezierCurve.anchor_1.x
 
    result.y = pow(u, 3) * (bezierCurve.anchor_2.y + 3 * (bezierCurve.control_1.y - bezierCurve.control_2.y) - bezierCurve.anchor_1.y) \
               + 3 * pow(u, 2) * (bezierCurve.anchor_1.y - 2 * bezierCurve.control_1.y + bezierCurve.control_2.y) \
               + 3 * u * (bezierCurve.control_1.y - bezierCurve.anchor_1.y) + bezierCurve.anchor_1.y
    
    return result


""" method to camathlculate the tangent of a point of a bezier curve 

:param u: position of the curve which we want to calculate, from 0 to 1
:type u: float
:param bezierCurve: coords of the start point, end point and tangent for each of them for the curve
:type bezierCurve: bezier_curve.msg.BezierCurve
:returns: result tangente
:rtype: float
"""
def getBezierCurveTangentResult(u, bezierCurve):
    p = PointMsg()
    alphaX = (bezierCurve.anchor_2.x + 3 * (bezierCurve.control_1.x - bezierCurve.control_2.x) - bezierCurve.anchor_1.x)
    alphaY = (bezierCurve.anchor_2.y + 3 * (bezierCurve.control_1.y - bezierCurve.control_2.y) - bezierCurve.anchor_1.y)
    betaX = (bezierCurve.anchor_1.x - 2 * bezierCurve.control_1.x + bezierCurve.control_2.x)
    betaY = (bezierCurve.anchor_1.y - 2 * bezierCurve.control_1.y + bezierCurve.control_2.y)
    gammaX = (bezierCurve.control_1.x - bezierCurve.anchor_1.x)
    gammaY = (bezierCurve.control_1.y - bezierCurve.anchor_1.y)
    
    p.x = 3 * pow(u, 2) * alphaX + 6 * u * betaX + 3 * gammaX
    p.y = 3 * pow(u, 2) * alphaY + 6 * u * betaY + 3 * gammaY
    tangent = math.atan2(p.y, p.x)
    
    return tangent


""" method to calculate the length of a BezierPath 

:param s: position of the curve which we want to calculate, from 0 to 1
:type s: float
:param bezierCurve: coords of the start point, end point and tangent for each of them for the curve
:type bezierCurve: bezier_curve.msg.BezierCurve
:returns: result length
:rtype: float
"""
def getBezierCurveLength(bezierCurve):
    ds = 0.001
    length = 0.0
    
    s = 0.0
    p = PoseMsg()
    
    p.position = getBezierCurveResult(s, bezierCurve)
    s += ds
    
    while s <= 1.0:  
        x_old = p.position.x
        y_old = p.position.y
        p.position = getBezierCurveResult(s, bezierCurve)
        
        dx = p.position.x - x_old
        dy = p.position.y - y_old
        dl = math.sqrt(dx*dx + dy*dy)
        length += dl
        
        s += ds
            
    return length


if __name__ == "__main__":
    rospy.init_node('bezier_interpolate', anonymous = True)
    
    rospy.Subscriber("scenario", ScenarioMsg, scenarioCallback)
    
    pathPublisher = rospy.Publisher("path", PathMsg)
    speedPublisher = rospy.Publisher("linear_speed", Float64Msg)
    
    step = rospy.get_param("bezier_curve_step", DEFAULT_BEZIER_CURVE_STEP)
    stepInMeter = rospy.get_param("bezier_curve_step_in_meter", DEFAULT_BEZIER_CURVE_STEP)
    
    rospy.spin()
