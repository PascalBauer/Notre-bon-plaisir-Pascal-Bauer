#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from functools import partial
import math

import rospkg
import rospy
import tf

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic

from src.robot.src import utils
from std_msgs.msg import Bool as BoolMsg
from scenario_msgs.msg import Scenario as ScenarioMsg
from src.scenario_lib.src.items.robot import Robot
from src.scenario_lib.src.items.media import Media
from src.scenario_lib.src.items.scenario import Scenario
from src.bezier_curve.src import bezier_interpolate

from canvas import Canvas
from robotMediaPlayer import RobotMediaPlayer
from temporalization import Temporalization
from sequences import Sequences


class ScenarioEdition():
    ALL_LABEL = "tous"
    scenarioUid = 0
    
    def __init__(self, scenarioFilePath = None, saveCallback = None, closeCallback = None):
        self.currentScenario = None
        self.currentFilePath = None
        self.lastChangesSaved = True
        
        self.saveCallback = saveCallback
        self.closeCallback = closeCallback
        
        try:
            ui_file = os.path.join(rospkg.RosPack().get_path('gui_scenario_builder'), 'resource', 'scenario_edition.ui')
            self.numMaxRobots = rospy.get_param("num_robots")
            self.monitorScreenWidth = rospy.get_param("monitor_screen_width")
            self.monitorScreenHeight = rospy.get_param("monitor_screen_height")
            self.monitorScreenResolutionWidth = rospy.get_param("monitor_screen_resolution_width")
            self.monitorScreenResolutionHeight = rospy.get_param("monitor_screen_resolution_height")
        except Exception:
            ui_file = os.path.expanduser("~") + "/catkin_ws/src/gui_scenario_builder/resource/scenario_edition.ui"
            self.numMaxRobots = 7
            self.monitorScreenWidth = 35
            self.monitorScreenHeight = 55
            self.monitorScreenResolutionWidth = 1280
            self.monitorScreenResolutionHeight = 720
            
        # load ui
        self.ui = uic.loadUi(ui_file)
        
        # robots
        self.ui.robots_list.currentItemChanged.connect(self.handleRobotsListSelectionChanged)
        
        # canvas
        self.canvas = Canvas(self, self.ui, self.changeCallback)
        self.ui.layout().addWidget(self.canvas)
        
        # toggle points for editing
        self.actionButtons = {self.ui.addPoint_button: Canvas.ADD_ACTION, self.ui.removePoint_button: Canvas.REMOVE_ACTION}
        
        self.uncheckActionButtons()
        
        for actionButton in self.actionButtons.keys():
            actionButton.clicked.connect(partial(self.handleActionButtonClicked, actionButton))
        
        # media player
        self.robotMediaPlayer = RobotMediaPlayer(self.ui, self.canvas)
        
        # temporalization
        self.temporalization = Temporalization(self.ui, self.canvas, self.robotMediaPlayer, self.changeCallback)
        self.robotMediaPlayer.temporalization = self.temporalization
        
        # sequences
        self.sequences = Sequences(self.ui, self.canvas, self.temporalization)
        
        # physical robots
        self.transformListener = tf.TransformListener()
        self.transformPositions = {}
        self.transformOrientations = {}
        self.lookupTransformTimers = {}
        
        self.scenarioPublishers = {}
        self.freezePublishers = {}
        
        self.launchedRobots = utils.getLaunchedRobots()
        for launchedRobot in self.launchedRobots:
            robotId = "/" + launchedRobot
            self.ui.robotId_comboBox.addItem(robotId)
            
            self.scenarioPublishers[robotId] = rospy.Publisher(robotId + "/scenario", ScenarioMsg)
            self.freezePublishers[robotId] = rospy.Publisher(robotId + "/freeze", BoolMsg)
            
            self.transformPositions[robotId] = (0, 0, 0)
            self.transformOrientations[robotId] = (0, 0, 0, 1)
            
            # lookup transform initialization
            self.lookupTransformTimers[robotId] = QTimer()
            #self.lookupTransformTimers[robotId].setSingleShot(True)
            self.lookupTransformTimers[robotId].timeout.connect(partial(self.getRobotTransform, robotId))
            self.lookupTransformTimers[robotId].start(200)
            
        if len(self.launchedRobots) > 1:
            self.ui.robotId_comboBox.addItem(ScenarioEdition.ALL_LABEL)
        elif len(self.launchedRobots) <= 0:
            self.ui.testOnPhysicalRobot_button.setEnabled(False)
            
        # other buttons
        self.ui.showControls_button.clicked.connect(self.handleShowControlsButtonClicked)
        self.handleShowControlsButtonClicked(False)
        self.ui.breakTangent_button.clicked.connect(self.handleBreakTangentButtonClicked)
        self.handleBreakTangentButtonClicked(False)
        self.ui.mediaPositions_button.clicked.connect(self.handleMediaPositionsButtonClicked)
        self.handleMediaPositionsButtonClicked(False)
        self.ui.showMedia_button.clicked.connect(self.handleShowMediaButtonClicked)
        self.handleShowMediaButtonClicked(False)
        self.ui.addRobot_button.clicked.connect(self.handleAddRobotButtonClicked)
        
        self.ui.testOnPhysicalRobot_button.clicked.connect(self.handleTestOnPhysicalRobot)
        self.ui.stopPhysicalRobot_button.clicked.connect(self.handleStopPhysicalRobot)
        
        # button groups
        self.comportementButtonGroup = QButtonGroup()
        self.comportementButtonGroup.addButton(self.ui.calme_radioButton)
        self.comportementButtonGroup.addButton(self.ui.enerve_radioButton)
        self.comportementButtonGroup.addButton(self.ui.furieux_radioButton)
        self.comportementButtonGroup.setExclusive(True)
        
        self.ui.calme_radioButton.toggled.connect(partial(self.changeCallback))
        self.ui.enerve_radioButton.toggled.connect(partial(self.changeCallback))
        self.ui.furieux_radioButton.toggled.connect(partial(self.changeCallback))
        self.ui.definitif_checkbox.stateChanged.connect(partial(self.changeCallback))
        
        self.ui.audioFileBrowse_button.clicked.connect(partial(self.handleAudioFileBrowseButtonClicked))
        
        # menu
        self.ui.actionNew.triggered.connect(partial(self.newScenario))
        self.ui.actionOpen.triggered.connect(partial(self.openScenario))
        self.ui.actionSave.triggered.connect(partial(self.saveScenario))
        self.ui.actionSaveAs.triggered.connect(partial(self.saveAsScenario))
        self.ui.actionNew.setShortcut('Ctrl+N')
        self.ui.actionOpen.setShortcut('Ctrl+O')
        self.ui.actionSave.setShortcut('Ctrl+S')
        self.ui.actionSaveAs.setShortcut('Ctrl+Shift+S')
        
        # load data
        if scenarioFilePath is not None:
            self.currentFilePath = scenarioFilePath
            self.lastChangesSaved = True
            self.openScenario(self.currentFilePath)
            
            # remove menu options
            self.ui.actionNew.setVisible(False)
            self.ui.actionOpen.setVisible(False)
            self.ui.actionSaveAs.setVisible(False)
        else:
            self.newScenario()
        
        self.ui.resizeEvent = self.resizeEvent
        self.ui.closeEvent = self.closeEvent
        self.ui.mousePressEvent = self.mousePressEvent
        self.ui.show()
        self.resizeEvent()
    
    
    # menu actions
    def newScenario(self):
        self.loadScenario(Scenario())
        self.lastChangesSaved = True
        self.updateWindowTitle()
        
    
    def openScenario(self, filePathToOpen = None):
        if filePathToOpen is None or filePathToOpen == False:
            # hide and show because of a bug which shows a blank qfiledialog
            self.canvas.hide()
            filePathToOpen = str(QFileDialog.getOpenFileName(self.ui, u"Ajouter un média", "", u"Scénario: *.sce (*.sce)").toUtf8())
            self.canvas.show()
        
        if filePathToOpen != "":
            self.currentFilePath = filePathToOpen
            scenarioToOpen = Scenario.loadFile(self.currentFilePath)
            self.loadScenario(scenarioToOpen)
            self.lastChangesSaved = True
            self.updateWindowTitle()
        
    
    def saveScenario(self):
        if self.currentFilePath is None:
            self.saveAsScenario()
        else:
            self.currentScenario.setAttributes(self.getAttributes())
            self.currentScenario.save(self.currentFilePath, self.canvas.getGridSize())
            self.lastChangesSaved = True
            self.updateWindowTitle()
        
        # notify the db application (after saving to update attributes var)
        if self.saveCallback is not None:
            self.saveCallback(self.currentFilePath, self.currentScenario)
        
    
    def saveAsScenario(self):
        # hide and show because of a bug which shows a blank qfiledialog
        self.canvas.hide()
        filePathToOpen = str(QFileDialog.getSaveFileName(self.ui, u"Sauvegarder le scénario", "", u"Scénario: *.sce (*.sce)").toUtf8())
        self.canvas.show()
        
        filePathToOpen = filePathToOpen
            
        if filePathToOpen != "":
            if not filePathToOpen.endswith(".sce"):
                filePathToOpen += ".sce"
            self.currentFilePath = filePathToOpen
            self.saveScenario()
            self.lastChangesSaved = True
        
    
    def loadScenario(self, scenario):
        del self.currentScenario
        
        self.currentScenario = scenario
        self.setAttributes(scenario.getAttributes())
        self.canvas.currentRobot = self.currentScenario.robots[0]
        
        # update
        self.updateRobots()
        self.temporalization.update()
        self.canvas.update()
        self.lastChangesSaved = True
    
    
    def changeCallback(self):
        self.lastChangesSaved = False
        self.updateWindowTitle()
        #self.currentScenario.gridSize = self.canvas.getGridSize()
    
    
    def handleAudioFileBrowseButtonClicked(self):
        fileName = QFileDialog.getOpenFileName(None, 'Fichier Audio', os.path.expanduser("~"))
        if fileName is not None:
            self.ui.audioFile_lineEdit.setText(fileName)
            self.lastChangesSaved = False
            self.updateWindowTitle()
        
    
    def updateWindowTitle(self):
        if self.currentFilePath is not None:
            currentFilePath = self.currentFilePath.decode("utf-8")
        else:
            currentFilePath = None
        self.ui.setWindowTitle(u"Édition de scénario - " + ("*" if not self.lastChangesSaved else "") + (currentFilePath if currentFilePath is not None else u"nouveau scénario"))
        
    
    def getAttributes(self):
        result = {}
        result["comportement"] = str(self.comportementButtonGroup.checkedButton().text().toUtf8())
        result["definitif"] = self.ui.definitif_checkbox.isChecked()
        result["fichier_audio"] = str(self.ui.audioFile_lineEdit.text())
        return result
        
    
    def setAttributes(self, attributes):
        if "comportement" in attributes:
            self.checkButtonGroupForAttributeValue(self.comportementButtonGroup, attributes["comportement"])
        else:
            self.comportementButtonGroup.buttons()[0].setChecked(True)
        if "definitif" in attributes:
            self.ui.definitif_checkbox.setChecked(attributes["definitif"])
        if "fichier_audio" in attributes:
            self.ui.audioFile_lineEdit.setText(attributes["fichier_audio"])
        else:
            self.ui.definitif_checkbox.setChecked(False)
        
    
    def checkButtonGroupForAttributeValue(self, buttonGroup, attributeValue):
        for radioButton in buttonGroup.buttons():
            if radioButton.text() == attributeValue:
                radioButton.setChecked(True)
                break
        
        
    def updateRobots(self):
        # get previous row
        previousSelection = self.ui.robots_list.selectedItems()
        previousSelectedRow = 0
        if len(previousSelection) > 0:
            previousSelectedRow = self.ui.robots_list.indexFromItem(previousSelection[0]).row()
        
        # limit number of robots
        self.ui.addRobot_button.setEnabled(len(self.currentScenario.robots) < self.numMaxRobots)
        # clear and rebuild everything
        self.ui.robots_list.clear()
        for i in range(len(self.currentScenario.robots)):
            robot = self.currentScenario.robots[i]
            
            itemWidget = QWidget()
            itemWidget.setLayout(QHBoxLayout())
            
            colorWidget = QWidget()
            colorWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            colorWidget.setMinimumSize(15, 15)
            colorWidget.setStyleSheet("background: " + robot.color.name() + ";")
            label = QLabel("Robot " + str(i + 1))
            visibleCheckbox = QCheckBox("visible")
            visibleCheckbox.setChecked(True)
            visibleCheckbox.setFocusPolicy(Qt.NoFocus)
            visibleCheckbox.stateChanged.connect(partial(self.handleVisibleCheckboxChanged, visibleCheckbox, robot))
            deleteButton = QPushButton("Supprimer")
            if len(self.currentScenario.robots) <= 1:
                deleteButton.setEnabled(False)
            deleteButton.clicked.connect(partial(self.handleRemoveRobotButton, robot))
            deleteButton.setFocusPolicy(Qt.NoFocus)
            itemWidget.layout().addWidget(colorWidget)
            itemWidget.layout().addWidget(label)
            itemWidget.layout().addWidget(visibleCheckbox)
            itemWidget.layout().addWidget(deleteButton)
            itemWidget.layout().setContentsMargins(9, 2, 2, 2)
            
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 27))
            
            self.ui.robots_list.addItem(item)
            self.ui.robots_list.setItemWidget(item, itemWidget)
        
        # if not, select first item
        self.ui.robots_list.setCurrentRow(previousSelectedRow)
        
        
    def getRobotTransform(self, robotId):
        try:
            self.transformPositions[robotId], self.transformOrientations[robotId] = self.transformListener.lookupTransform("/map", robotId + "/base_link", rospy.Time(0))
        except Exception, e:
            rospy.logerr(e)
            
            
    def closeEvent(self, event = None):
        if self.closeCallback is not None:
            self.closeCallback(self.currentFilePath)
        
    
    def mousePressEvent(self, event):
        focusedWidget = QApplication.focusWidget()
        if focusedWidget is not None:
            focusedWidget.clearFocus()
        QMainWindow.mousePressEvent(self.ui, event)
    
    
    def resizeEvent(self, event = None):
        # canvas
        absoluteCoords = self.ui.canvasContainer.mapToGlobal(QPoint(0, 0))
        absoluteCoords -= self.ui.mapToGlobal(QPoint(0, 0))
        self.canvas.setGeometry(absoluteCoords.x(), absoluteCoords.y(), self.ui.canvasContainer.width(), self.ui.canvasContainer.height())
        self.canvas.update()
        
        # media
        #self.ui.mediaContainer_widget.setMaximumHeight(self.ui.mediaContainer_widget.width() * (float(self.monitorScreenResolutionHeight) / float(self.monitorScreenResolutionWidth)))
    
    
    # buttons
    def uncheckActionButtons(self):
        self.canvas.currentAction = -1
        self.ui.addPoint_button.setChecked(False)
        self.ui.removePoint_button.setChecked(False)
        
        
    def handleActionButtonClicked(self, button):
        if button.isChecked():
            for actionButton in self.actionButtons.keys():
                if actionButton != button:
                    actionButton.setChecked(False)
        
            self.canvas.currentAction = self.actionButtons[button]
        else:
            self.canvas.currentAction = -1
        
    
    def handleShowControlsButtonClicked(self, event):
        self.canvas.showControls = self.ui.showControls_button.isChecked()
        self.canvas.update()
        
        
    def handleBreakTangentButtonClicked(self, event):
        self.canvas.breakTangent = self.ui.breakTangent_button.isChecked()
    
    
    def handleRobotsListSelectionChanged(self, item):
        index = self.ui.robots_list.indexFromItem(item).row()
        if index >= 0:
            self.canvas.currentRobot = self.currentScenario.robots[index]
            self.canvas.otherRobots = [robot for robot in self.currentScenario.robots if robot.visible]
            self.canvas.update()
            
            self.temporalization.update()
            self.sequences.update()
        
    
    def handleAddRobotButtonClicked(self, event):
        self.currentScenario.robots.append(Robot(self.currentScenario))
        
        self.updateRobots()
    
    
    def handleVisibleCheckboxChanged(self, checkbox, robot):
        robot.visible = checkbox.isChecked()
        self.canvas.otherRobots = [robot for robot in self.currentScenario.robots if robot.visible]
        self.canvas.update()
        
        
    def handleRemoveRobotButton(self, robotToRemove):
        self.currentScenario.robots.remove(robotToRemove)
        
        self.updateRobots()
    
    
    def handleMediaPositionsButtonClicked(self, event):
        self.canvas.showTemporalization = self.ui.mediaPositions_button.isChecked()
        self.canvas.update()
        
    
    def handleShowMediaButtonClicked(self, event):
        self.canvas.showMedia = self.ui.showMedia_button.isChecked()
    
    
    def handleTestOnPhysicalRobot(self):
        robotId = str(self.ui.robotId_comboBox.currentText())
        
        waitAfterStartTime = self.ui.waitAfterStartTime_spinBox.value()
        
        if robotId == ScenarioEdition.ALL_LABEL:
            scenarioRobotIndex = 0
            
            for launchedRobot in self.launchedRobots:
                robotId = "/" + launchedRobot
                robot = self.currentScenario.robots[scenarioRobotIndex]
                
                scenarioMsg = robot.getScenarioMsgWithParams(self.transformPositions[robotId], 1. / float(self.currentScenario.gridSize), self.transformOrientations[robotId], True, False, waitAfterStartTime)
                
                scenarioMsg.uid = ScenarioEdition.scenarioUid
                ScenarioEdition.scenarioUid += 1
                
                rospy.loginfo(str(scenarioMsg))
                self.scenarioPublishers[robotId].publish(scenarioMsg)
                
                scenarioRobotIndex += 1
                if scenarioRobotIndex >= len(self.currentScenario.robots):
                    break
        else:
            scenarioMsg = self.canvas.currentRobot.getScenarioMsgWithParams(self.transformPositions[robotId], 1. / float(self.currentScenario.gridSize), self.transformOrientations[robotId], True, False, waitAfterStartTime)
            
            scenarioMsg.uid = ScenarioEdition.scenarioUid
            ScenarioEdition.scenarioUid += 1
                
            rospy.loginfo(str(scenarioMsg))
            self.scenarioPublishers[robotId].publish(scenarioMsg)

    def handleStopPhysicalRobot(self):
        freezeMsg = BoolMsg()
        freezeMsg.data = True
        
        robotId = str(self.ui.robotId_comboBox.currentText())
        if robotId == ScenarioEdition.ALL_LABEL:
            for launchedRobot in self.launchedRobots:
                robotId = "/" + launchedRobot
                self.freezePublishers[robotId].publish(freezeMsg)
        else:
            self.freezePublishers[robotId].publish(freezeMsg)
            