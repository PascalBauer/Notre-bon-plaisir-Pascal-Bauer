#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import json

from robot import Robot
from media import Media

class Scenario():
    def __init__(self, loadWithVideos = True):
        Robot.reinit()
        Media.reinit()
        
        self.creationTime = time.time()
        self.modificationTime = time.time()
        self.loadWithVideos = loadWithVideos
        
        self.robots = [Robot(loadWithVideos)]
        
        self.name = None
        self.attributes = []
    
    
    def getAttributes(self):
        return self.attributes
    
    
    def setAttributes(self, attributes):
        self.attributes = attributes
    
    
    def getDataDict(self, scale = 1):
        data = {}
        data["creationTime"] = self.creationTime
        data["modificationTime"] = time.time()
        data["robots"] = [robot.save(scale) for robot in self.robots]
        data["attributes"] = self.attributes
        
        return data
    
    
    def setDataDict(self, data):
        self.creationTime = data["creationTime"]
        self.modificationTime = data["modificationTime"]
        self.robots = []
        for robotData in data["robots"]:
            robotToAppend = Robot(self.loadWithVideos)
            robotToAppend.load(robotData)
            self.robots.append(robotToAppend)
        self.attributes = data["attributes"]
    
    
    def save(self, filePath, scale = 1):
        self.name = os.path.basename(str(filePath))
        
        with open(filePath, 'w') as outFile:
            json.dump(self.getDataDict(scale), outFile)
    
    
    def toScenarioMsg(self):
        return None
    
    
    @staticmethod
    def loadFile(filePath, loadWithVideos = True):
        data = json.loads(open(filePath).read())
        scenario = Scenario(loadWithVideos)
        scenario.name = os.path.basename(str(filePath))
        scenario.setDataDict(data)
        
        return scenario
