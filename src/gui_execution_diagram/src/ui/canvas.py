import os
import shutil
from functools import partial
import math
import json

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from src.scenario_lib.src.items import nodes
from src.scenario_lib.src.items.nodes.diagramNode import DiagramNode
from src.scenario_lib.src.items.nodes.nodeException import NodeException

class Canvas(QWidget):
    grey = QColor(100, 100, 100)
    linkColor = QColor(79, 128, 255)
    executingLinkColor = QColor(255, 255, 0)
    linkPen = QPen(linkColor)
    
    def __init__(self, ui, changeCallback):
        super(QWidget, self).__init__()
        
        self.ui = ui
        self.changeCallback = changeCallback
        
        Canvas.linkPen.setCapStyle(Qt.SquareCap);
        Canvas.linkPen.setWidth(2);
        
        # ui
        self.currentLink = None
        self.nodeWidgetUnderMouse = None
        
        # context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.handleContextMenuRequested)
        
        # vars
        self.nodesInstances = []
        
        self.updateBounds()
            
    
    def paintEvent(self, e):
        # paint it
        painter = QPainter(self)

        self.drawBackground(painter)
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        self.drawLinks(painter)
        
        
    def drawBackground(self, painter):
        painter.fillRect(QRectF(0, 0, self.width(), self.height()), Canvas.grey)
        
        
    def drawLinks(self, painter):
        if self.currentLink is not None:
            self.drawLink(painter, self.currentLink[0], self.currentLink[1])
        
        for nodeInstance in self.nodesInstances:
            if self.currentLink is None and nodeInstance.outputWidget is not None:
                nodeInstance.outputWidget.button.setDown(False)
            for inputWidget in nodeInstance.getInputsWidgets():
                if inputWidget.connectedToInstance is not None:
                    self.drawLink(painter, inputWidget.button, inputWidget.connectedToInstance)
        
        if self.currentLink is None:
            for nodeInstance in self.nodesInstances:
                try:
                    nodeInstanceInputs = nodeInstance.getInputs()
                    for nodeInstanceInput in nodeInstanceInputs:
                        if nodeInstanceInput.outputWidget is not None:
                            nodeInstanceInput.outputWidget.button.setDown(True)
                except NodeException:
                    pass
        
    
    def drawLink(self, painter, inputButton, target):
        # set down the input button
        inputButton.setDown(True)
        
        # get center of input button
        currentLinkStartPos = inputButton.parent().mapToGlobal(inputButton.pos()) - self.mapToGlobal(QPoint()) + QPoint(inputButton.width() / 2, inputButton.height() / 2)
        
        nodeWidgetUnderMouse = None
        executingLink = False
        
        # check if target is a point or a destination button
        if isinstance(target, QPoint):
            mousePos = target
            currentLinkEndPos = self.mapFromGlobal(mousePos)
            
            # get child under mouse
            nodeWidgetUnderMouse = self.getNodeWidgetUnderMouse(inputButton.parent().parent(), mousePos)
        elif isinstance(target, DiagramNode):
            nodeWidgetUnderMouse = target.widget
            
            # is the line between executing nodes
            executingLink = inputButton.objectName == "executing" and nodeWidgetUnderMouse.nodeInstance.outputWidget.button.objectName == "executing"
            
        # snap to it
        if nodeWidgetUnderMouse is not None:
            if nodeWidgetUnderMouse.nodeInstance.outputWidget is not None:
                middleButton = QPoint(nodeWidgetUnderMouse.nodeInstance.outputWidget.button.width() / 2, nodeWidgetUnderMouse.nodeInstance.outputWidget.button.height() / 2)
                currentLinkEndPos = middleButton + nodeWidgetUnderMouse.mapToGlobal(nodeWidgetUnderMouse.nodeInstance.outputWidget.pos()) - self.mapToGlobal(QPoint())
                nodeWidgetUnderMouse.nodeInstance.outputWidget.button.setDown(True)
                if not isinstance(target, DiagramNode): # if it is not for drawing a definitive link
                    self.nodeWidgetUnderMouse = nodeWidgetUnderMouse
        elif self.nodeWidgetUnderMouse is not None:
            self.nodeWidgetUnderMouse.nodeInstance.outputWidget.button.setDown(False)
            self.nodeWidgetUnderMouse = None
        
        # draw line
        linkColor = Canvas.linkColor if not executingLink else Canvas.executingLinkColor
        Canvas.linkPen.setColor(linkColor)
        painter.setPen(Canvas.linkPen)
        painter.drawLine(currentLinkStartPos, currentLinkEndPos)
        # draw direction triangle
        linkLine = currentLinkEndPos - currentLinkStartPos
        lineCenter = currentLinkStartPos + linkLine / 2
        angle = math.atan2(linkLine.y(), linkLine.x())
        triangleLength1 = 5.
        triangleLength2 = 10.
        angleTop = angle - math.pi / 2
        angleBottom = angle + math.pi / 2
        topTriangle = QPoint(triangleLength1 * math.cos(angleTop), triangleLength1 * math.sin(angleTop))
        bottomTriangle = QPoint(triangleLength1 * math.cos(angleBottom), triangleLength1 * math.sin(angleBottom))
        summitTriangle = lineCenter - QPoint(triangleLength2 * math.cos(angle), triangleLength2 * math.sin(angle))
        
        painter.setBrush(linkColor)
        painter.drawPolygon(QPolygon([summitTriangle, lineCenter + topTriangle, lineCenter + bottomTriangle, summitTriangle]))
        
    
    def setCurrrentLink(self, inputButton, position):
        if inputButton is None and position is None:
            self.currentLink = None
        else:
            self.currentLink = (inputButton, position)
        
        self.update()
    
    
    def getNodeWidgetUnderMouse(self, currentWidgetStartLink, currentPosEndLink):
        childUnderMouse = self.ui.childAt(self.ui.mapFromGlobal(currentPosEndLink))
        nodesWidgets = [nodeInstance.widget if nodeInstance.widget != currentWidgetStartLink.parent() else None for nodeInstance in self.nodesInstances]
        result = None
        while childUnderMouse is not None:
            if childUnderMouse in nodesWidgets:
                result = childUnderMouse
                break
            
            childUnderMouse = childUnderMouse.parent()
            
        return result
    
    
    def updateBounds(self):
        maxWidth = self.ui.canvasContainer.width()
        maxHeight = self.ui.canvasContainer.height()
        
        for nodeInstance in self.nodesInstances:
            nodeInstanceMaxWidth = nodeInstance.widget.x() + nodeInstance.widget.width()
            nodeInstanceMaxHeight = nodeInstance.widget.y() + nodeInstance.widget.height()
            if nodeInstanceMaxWidth > maxWidth:
                maxWidth = nodeInstanceMaxWidth
            if nodeInstanceMaxHeight > maxHeight:
                maxHeight = nodeInstanceMaxHeight
        self.setMinimumSize(maxWidth, maxHeight)
        self.setMaximumSize(maxWidth, maxHeight)
    
    
    def save(self, filePath):
        nodesDataList = []
        
        for nodeInstance in self.nodesInstances:
            nodeData = nodeInstance.getDataFromInstance()
            nodesDataList.append(nodeData)
        
        if os.path.exists(filePath):
            # make a backup
            i = 0
            while True:
                backupFilePath = filePath.replace(os.path.basename(filePath), "." + os.path.basename(filePath)) + "." + str(i) + ".history"
                
                if not os.path.exists(backupFilePath):
                    break
                
                i += 1
                
            shutil.copy(filePath, backupFilePath)
        
        with open(filePath, 'w') as outFile:
            json.dump(nodesDataList, outFile)
        
        outFile.close()
    
    
    def load(self, filePath):
        # remove all nodes
        for nodeInstanceIndex in range(len(self.nodesInstances)):
            nodeInstance = self.nodesInstances[0]
            nodeInstance.widget.setParent(None)
            nodeInstance.widget.hide()
            nodeInstance.destroy()
            del self.nodesInstances[0]
        self.nodesInstances = []
        
        DiagramNode.currentNodeId = 0
        
        # get file data
        if filePath is None:
            nodesDataList = []
        else:
            nodesDataList = json.loads(open(filePath).read())
        
        # instantiate nodes
        for nodeData in nodesDataList:
            nodeInstance = DiagramNode.createInstanceFromData(self, nodeData)
            self.nodesInstances.append(nodeInstance)
        
        # make connections
        for nodeData in nodesDataList:
            DiagramNode.linkInstanceFromData(self, nodeData)
                
        self.update()
        self.updateBounds()
            
    
    def getNodeInstanceById(self, nodeId):
        for nodeInstance in self.nodesInstances:
            if nodeInstance.id == nodeId:
                return nodeInstance
    
        return None
    
    
    # context menu
    def handleContextMenuRequested(self, position):
        # get nodes
        nodesDict = {}
        for nodeClass in nodes.getAllDiagramNodesClasses('nodes'):
            if not nodeClass.nodeCategory in nodesDict:
                nodesDict[nodeClass.nodeCategory] = [] 
            nodesDict[nodeClass.nodeCategory].append(nodeClass)
        
        # make menu
        menu = QMenu()
        nodesCategories = nodesDict.keys()
        nodesCategories.sort()
        
        for robotId in ["robot01", "robot02", "robot03"]:
            robotMenu = menu.addMenu(robotId)
            for nodeCategory in nodesCategories:
                if nodeCategory == "":
                    for nodeClass in nodesDict[nodeCategory]:
                        if nodeClass.nodeName != "":
                            menuAction = robotMenu.addAction(nodeClass.nodeName)
                            menuAction.triggered.connect(partial(self.handleMenuActionTriggered, nodeClass, robotId, position))
        
        menu.exec_(self.mapToGlobal(position))
    
    
    def handleMenuActionTriggered(self, nodeClass, robotId, position):
        nodeInstance = nodeClass(robotId, self.ui.canvasContainer, self, position)
        nodeInstance.widget.move(position.x() - nodeInstance.widget.width() / 2, position.y() - 10)
        self.nodesInstances.append(nodeInstance)
        
        
        