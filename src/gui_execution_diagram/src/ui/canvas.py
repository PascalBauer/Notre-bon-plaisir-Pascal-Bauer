from functools import partial
import math

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from src.scenario_lib.src.items import nodes
from src.scenario_lib.src.items.nodes.diagramNode import DiagramNode

class Canvas(QWidget):
    grey = QColor(100, 100, 100)
    linkColor = QColor(79, 128, 255)
    linkPen = QPen(linkColor)
    
    def __init__(self, ui, changeCallback):
        super(QWidget, self).__init__()
        
        self.ui = ui
        self.changeCallback = changeCallback
        
        Canvas.linkPen.setCapStyle(Qt.SquareCap);
        Canvas.linkPen.setWidth(2);
        
        # ui
        self.currentLink = None
        self.definitiveLinks = {}
        self.nodeWidgetUnderMouse = None
        
        # context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.handleContextMenuRequested)
        
        # vars
        self.nodesInstances = []
            
    
    def paintEvent(self, e):
        painter = QPainter(self)

        self.drawBackground(painter)
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        self.drawLinks(painter)
        
        
    def drawBackground(self, painter):
        painter.fillRect(QRectF(0, 0, self.width(), self.height()), Canvas.grey)
        
        
    def drawLinks(self, painter):
        painter.setPen(Canvas.linkPen)
        
        if self.currentLink is not None:
            self.drawLink(painter, self.currentLink[0], self.currentLink[1])
        
        for definitiveLinkInput, definitiveLinkOutput in self.definitiveLinks.items():
            self.drawLink(painter, definitiveLinkInput, definitiveLinkOutput)
    
    
    def drawLink(self, painter, inputButton, target):
        # set down the input button
        inputButton.setDown(True)
        
        # get center of input button
        currentLinkStartPos = inputButton.parent().mapToGlobal(inputButton.pos()) - self.mapToGlobal(QPoint()) + QPoint(inputButton.width() / 2, inputButton.height() / 2)
        
        nodeWidgetUnderMouse = None
        
        # check if target is a point or a destination button
        if isinstance(target, QPoint):
            mousePos = target
            currentLinkEndPos = self.mapFromGlobal(mousePos)
            
            # get child under mouse
            nodeWidgetUnderMouse = self.getNodeWidgetUnderMouse(inputButton.parent().parent(), mousePos)
        elif isinstance(target, DiagramNode):
            nodeWidgetUnderMouse = target.widget
            
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
        painter.drawLine(currentLinkStartPos, currentLinkEndPos)
        # draw direction triangle
        linkLine = currentLinkEndPos - currentLinkStartPos
        lineCenter = currentLinkStartPos + linkLine / 2
        painter.setBrush(Canvas.linkColor)
        angle = math.atan2(linkLine.y(), linkLine.x())
        triangleLength1 = 5.
        triangleLength2 = 10.
        angleTop = angle - math.pi / 2
        angleBottom = angle + math.pi / 2
        topTriangle = QPoint(triangleLength1 * math.cos(angleTop), triangleLength1 * math.sin(angleTop))
        bottomTriangle = QPoint(triangleLength1 * math.cos(angleBottom), triangleLength1 * math.sin(angleBottom))
        summitTriangle = lineCenter - QPoint(triangleLength2 * math.cos(angle), triangleLength2 * math.sin(angle))
        
        painter.drawPolygon(QPolygon([summitTriangle, lineCenter + topTriangle, lineCenter + bottomTriangle, summitTriangle]))
        
    
    def setCurrrentLink(self, inputButton, position):
        if inputButton is None and position is None:
            self.currentLink = None
        else:
            self.currentLink = (inputButton, position)
        
        self.update()
    
    
    def addDefinitiveLink(self, inputButton, outputButton):
        self.definitiveLinks[inputButton] = outputButton
        
        self.update()
    
    
    def deleteDefinitiveLinkFromInput(self, inputButton):
        if inputButton in self.definitiveLinks:
            del self.definitiveLinks[inputButton]
        
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
        for nodeCategory in nodesCategories:
            if nodeCategory == "":
                for nodeClass in nodesDict[nodeCategory]:
                    menuAction = menu.addAction(nodeClass.nodeName)
                    menuAction.triggered.connect(partial(self.handleMenuActionTriggered, nodeClass, position))
        
        menu.exec_(self.mapToGlobal(position))
    
    
    def handleMenuActionTriggered(self, nodeClass, position):
        nodeInstance = nodeClass(self.ui, self, position)
        self.nodesInstances.append(nodeInstance)
        
        
        