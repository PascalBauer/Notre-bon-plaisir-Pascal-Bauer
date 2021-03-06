#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtGui import *

from src.scenario_lib.src.items.nodes.diagramNode import DiagramNode
from src.scenario_lib.src.items.nodes.nodeException import NodeException

class SequenceNode(DiagramNode):
    nodeName = "Sequence"
    nodeCategory = ""
    
    maxInputs = 50
    minInputs = 1
    hasOutput = 1
    
    def __init__(self, robotId, parent, canvas, position):
        super(SequenceNode, self).__init__(robotId, parent, canvas, position)
        
        self.currentInputIndex = 0
        self.numInputs = 0
        
        # ui
        self.currentInputIndex_label = QLabel("en cours: " + str(self.currentInputIndex + 1))
        self.widget.central_widget.layout().addWidget(self.currentInputIndex_label)
        
    
    def output(self, args, updateRatioCallback):
        self.updateCallback = updateRatioCallback
        
        inputs = self.getInputs()
        self.numInputs = len(inputs)
        
        self.currentInputIndex += 1
        if self.currentInputIndex >= len(inputs): # in case of intended index has been removed
            self.currentInputIndex = 0
        inputItem = inputs[self.currentInputIndex]
        
        if updateRatioCallback is not None:
            # dry run
            self.startExecution(self.getInputWidgetIndexFromInputIndex(self.currentInputIndex))
        
        return inputItem.output(args, self.updateRatio if updateRatioCallback is not None else None)
    
    
    def updateRatio(self, inputRatio, paused):
        inputRatio = float(inputRatio)
        
        # get sequence ratio
        sequenceRatio = (float(self.currentInputIndex) / (self.numInputs)) + (inputRatio / self.numInputs)
        
        if inputRatio >= 1:
            # reset index
            if self.currentInputIndex >= self.numInputs:
                self.currentInputIndex = 0
        
        if sequenceRatio >= 1:
            # stop sequence
            self.stopExecution()
            self.updateCallback(1, True)
        else:
            if inputRatio >= 1 or paused:
                # send pause
                self.stopExecution()
                self.updateCallback(sequenceRatio, True)
            else:
                # continue
                self.updateCallback(sequenceRatio, False)
                self.setTimelineValue(sequenceRatio)
        
        # refresh ui counter
        self.currentInputIndex_label.setText("en cours: " + str(self.currentInputIndex + 1))
    
    
    def stop(self):
        super(SequenceNode, self).stop()
        
        #self.currentInputIndex = 0
    
    
    def getSpecificsData(self):
        return None
    
    
    def setSpecificsData(self, data):
        pass
        
        