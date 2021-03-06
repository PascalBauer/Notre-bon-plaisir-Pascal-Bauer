#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import json
import shutil

from robot import Robot
from media import Media

class Scenario():
    def __init__(self, loadWithVideos = True):
        Robot.reinit()
        Media.reinit()
        
        self.creationTime = time.time()
        self.modificationTime = time.time()
        self.gridSize = 10
        self.loadWithVideos = loadWithVideos
        
        self.targetPosition = [10, 10]
        self.robots = [Robot(self)]
        
        self.transformPosition = (0, 0, 0)
        self.transformOrientation = (1, 0, 0, 0)
        
        self.name = None
        self.attributes = {}
        
        self.checkedChoregraphicPath = None
        
        self.scenarioType = "choregraphic"
    
    
    def getAttributes(self):
        return self.attributes
    
    
    def setAttributes(self, attributes):
        self.attributes = attributes
    
    
    def getDataDict(self, gridSize):
        data = {}
        data["creationTime"] = self.creationTime
        data["modificationTime"] = time.time()
        data["gridSize"] = gridSize
        self.gridSize = gridSize
        data["targetPosition"] = self.targetPosition
        data["robots"] = [robot.save() for robot in self.robots]
        data["attributes"] = self.attributes
        
        return data
    
    
    def setDataDict(self, data):
        self.creationTime = data["creationTime"]
        self.modificationTime = data["modificationTime"]
        self.gridSize = data["gridSize"]
        self.robots = []
        for robotData in data["robots"]:
            robotToAppend = Robot(self)
            robotToAppend.load(robotData)
            self.robots.append(robotToAppend)
        self.targetPosition = data["targetPosition"]
        self.attributes = data["attributes"]
    
    
    def save(self, filePath, gridSize = 10):
        if os.path.exists(filePath):
            # make a backup
            i = 0
            while True:
                backupFilePath = str(filePath).replace(os.path.basename(filePath), "." + os.path.basename(filePath)) + "." + str(i) + ".history"
                if not os.path.exists(backupFilePath):
                    break
                
                i += 1
                
            shutil.copy(filePath, backupFilePath)
        
        self.name = os.path.basename(str(filePath))
        
        with open(filePath, 'w') as outFile:
            json.dump(self.getDataDict(gridSize), outFile)
        
        outFile.close()
    
    
    def loadVideos(self):
        for robot in self.robots:
            robot.loadVideos()
        
    
    def toScenarioMsg(self):
        return None
    
    
    def niceName(self):
        return (self.name[:-4] if "." in self.name else self.name).decode("utf-8")
    
    
    def getDuration(self):
        result = 0.
        
        for robot in self.robots:
            robotDuration = robot.getDuration()
            if robotDuration > result:
                result = robotDuration
        
        return result
            
    
    @staticmethod
    def loadFile(data, loadWithVideos = True):
        if type(data) == list or type(data) == tuple:
            filePath = data[0]
        else:
            filePath = data
        outfile = open(filePath)
        data = json.loads(outfile.read())
        scenario = Scenario(loadWithVideos)
        scenario.name = os.path.basename(str(filePath))
        scenario.setDataDict(data)
        
        outfile.close()
        
        return scenario
