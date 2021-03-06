#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from PyQt4.QtGui import *

from src.scenario_lib.src.items.nodes.diagramNode import DiagramNode
from src.scenario_lib.src.items.nodes.choregraphicScenarioNode import ChoregraphicScenarioNode
from src.scenario_lib.src.items.nodes.playNode import PlayNode
from src.scenario_lib.src.items.nodes.nodeException import NodeException
from src.scenario_lib.src.items.robot import Robot

class MasteringNode(DiagramNode):
    nodeName = u"Mastering"
    nodeCategory = ""
    
    maxInputs = 50
    minInputs = 1
    hasOutput = 1
    
    def __init__(self, robotId, parent, canvas, position):
        super(MasteringNode, self).__init__(robotId, parent, canvas, position)
        
    
    def output(self, args, updateRatioCallback):
        self.updateCallback = updateRatioCallback
        
        inputs = self.getInputs()
        
        indexOutput = 0
        
        # first index if nobody is mastering, else the same node
        if self.robotId != Robot.DEFAULT_ROBOT_ID:
            # get mastering scenarios
            for nodeInstance in self.canvas.nodesInstances:
                if type(nodeInstance) == PlayNode and nodeInstance.robotId == Robot.DEFAULT_ROBOT_ID:
                    if nodeInstance.playingScenario is not None and type(nodeInstance.playingScenario.originNode) == ChoregraphicScenarioNode and nodeInstance.playingScenario.originNode.isMastering:
                        i = 0
                        for newNodeInstance in inputs:
                            if newNodeInstance.masterId == nodeInstance.playingScenario.originNode.id:
                                indexOutput = i
                                break
                            i += 1
                if indexOutput != 0:
                    break
        
        inputItem = inputs[indexOutput]
        
        if updateRatioCallback is not None:
            # dry run
            self.startExecution(self.getInputWidgetIndexFromInputIndex(indexOutput))
        
        return inputItem.output(args, self.updateRatio if updateRatioCallback is not None else None)
    
    
    def updateRatio(self, inputRatio, paused):
        if inputRatio >= 1 or paused:
            self.stopExecution()
            self.updateCallback(inputRatio, True)
        else:
            self.updateCallback(inputRatio, False)
            self.setTimelineValue(inputRatio)
        return inputRatio
    
    
    def getSpecificsData(self):
        return None
    
    
    def setSpecificsData(self, data):
        pass
        
        