#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtGui import *

from src.scenario_lib.src.items.nodes.diagramNode import DiagramNode
from src.scenario_lib.src.items.nodes.nodeException import NodeException

class PlayNode(DiagramNode):
    nodeName = "Play"
    nodeCategory = ""
    
    maxInputs = 1
    minInputs = 1
    hasOutput = 0
    inputGroup = [""]
    
    def __init__(self, parent, canvas, position):
        super(PlayNode, self).__init__(parent, canvas, position)
        
        self.playingScenario = None
        
        self.playButton = QPushButton("Play")
        self.playButton.clicked.connect(self.handlePlayButtonClicked)
        self.widget.central_widget.layout().addWidget(self.playButton)
        self.playingScenarioLabel = QLabel("")
        self.widget.central_widget.layout().addWidget(self.playingScenarioLabel)
        self.stopButton = QPushButton("Stop")
        self.stopButton.clicked.connect(self.handleStopButtonClicked)
        self.stopButton.setEnabled(False)
        self.widget.central_widget.layout().addWidget(self.stopButton)
    
    
    def output(self):
        self.stopExecution()
        
        inputs = self.getInputs()
        
        self.startExecution(0)
        
        return inputs[0].output(self.updateRatio)
    
    
    def updateRatio(self, inputRatio, paused):
        if paused:
            self.playScenario(self.output())
            
            #self.playingScenario = None
            #self.playButton.setEnabled(True)
            #self.setTimelineValue(0)
            #self.playingScenarioLabel.setText("")
        else:
            self.setTimelineValue(inputRatio)
    
    
    def stop(self):
        super(PlayNode, self).stop()
        
        self.playingScenario = None
        self.playingScenarioLabel.setText("")
        
    
    def getSpecificsData(self):
        return None
    
    
    def setSpecificsData(self, data):
        pass
    
    
    def playScenario(self, scenario):
        try:
            self.playingScenario = scenario
            self.playingScenarioLabel.setText(self.playingScenario.name)
        except NodeException, e:
            print "Erreur: " + e.message
            self.stopAllScenarios()
    
    
    def stopAllScenarios(self):
        for nodeInstance in self.canvas.nodesInstances:
            nodeInstance.stop()
        
    
    def handlePlayButtonClicked(self, event):
        self.playButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        
        self.playScenario(self.output())
        
        
    def handleStopButtonClicked(self, event):
        self.playButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        
        self.stopAllScenarios()