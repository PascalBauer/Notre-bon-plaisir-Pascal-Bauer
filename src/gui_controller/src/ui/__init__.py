import os
from functools import partial
import math

import rospkg
import roslib
roslib.load_manifest('occupancy_grid_utils')

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic

from twistController import TwistController  # @UnresolvedImport
from canvas import Canvas
        
import occupancy_grid_utils
import occupancy_grid_utils_python as gu
import nav_msgs.msg as nm

class GuiController(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        
        
        map_info = nm.MapMetaData()
        map_info.resolution = 0.2
        map_info.origin.position.x = 1
        map_info.origin.position.y = 1
        map_info.origin.orientation.w = 1
        map_info.height = 20
        map_info.width = 20
        
        """grid = nm.OccupancyGrid()
        grid.info = map_info
        gu.allocate_grid(grid)
        
        def occ(i, j):
            gu.set_cell(grid, gu.Cell(i, j), gu.OCCUPIED)
        
        occ(1, 6)
        occ(3, 4)
        occ(3, 7)
        occ(4, 4)
        occ(4, 6)
        occ(5, 4)
        occ(7, 8)
        """
        """
        scan_info = gu.LaserScan()
        scan_info.angle_min = -math.pi/2
        scan_info.angle_max = math.pi/2
        scan_info.angle_increment = math.pi/4
        scan_info.range_max = 1.0"""
        
        sp = gu.make_pose(1.7, 1.9, math.pi/2)
        print sp
        
        return
        self.twistController = TwistController()
        
        try:
            ui_file = os.path.join(rospkg.RosPack().get_path('gui_controller'), 'resource', 'gui_controller.ui')
        except:
            ui_file = os.path.expanduser("~") + "/catkin_ws/src/gui_controller/resource/gui_controller.ui"
        
        self.ui = uic.loadUi(ui_file)
        self.ui.show()
        
        self.currentLinearSpeed = 0
        self.currentAngularSpeed = 0
        
        self.ui.goForward_button.pressed.connect(partial(self.handleButtonChanged, 1, 0))
        self.ui.goForward_button.released.connect(partial(self.handleButtonChanged, -1, 0))
        self.ui.goBackward_button.pressed.connect(partial(self.handleButtonChanged, -1, 0))
        self.ui.goBackward_button.released.connect(partial(self.handleButtonChanged, 1, 0))
        self.ui.turnLeft_button.pressed.connect(partial(self.handleButtonChanged, 0, 1))
        self.ui.turnLeft_button.released.connect(partial(self.handleButtonChanged, 0, -1))
        self.ui.turnRight_button.pressed.connect(partial(self.handleButtonChanged, 0, -1))
        self.ui.turnRight_button.released.connect(partial(self.handleButtonChanged, 0, 1))
        
        absoluteCoords = self.ui.canvasContainer.mapToGlobal(self.ui.pos())
        canvas = Canvas(self.handleCanvasCursorMoved, absoluteCoords.x(), absoluteCoords.y(), self.ui.canvasContainer.width(), self.ui.canvasContainer.height())
        self.ui.layout().addWidget(canvas)
        
        self.ui.keyPressEvent = self.keyPressEvent
        self.ui.keyReleaseEvent = self.keyReleaseEvent
    
    # keyboard
    def handleButtonChanged(self, linearSpeed, angularSpeed):
        inputLinearSpeed = float(self.ui.linearSpeed_slider.value()) / 10.
        inputAngularSpeed = 2 * float(self.ui.angularSpeed_slider.value()) / 10.
        self.currentLinearSpeed += linearSpeed
        self.currentAngularSpeed += angularSpeed
        self.twistController.move(self.currentLinearSpeed * inputLinearSpeed, self.currentAngularSpeed * inputAngularSpeed)
        
    
    def keyPressEvent(self, event):
        self.manageKey(event.key, True)
    
    
    def keyReleaseEvent(self, event):
        self.manageKey(event.key, False)
    
    
    def manageKey(self, key, pressed):
        button = None
        
        if key() == Qt.Key_Z:
            button = self.ui.goForward_button
        if key() == Qt.Key_S:
            button = self.ui.goBackward_button
        if key() == Qt.Key_Q:
            button = self.ui.turnLeft_button
        if key() == Qt.Key_D:
            button = self.ui.turnRight_button
        
        if button is not None:
            button.setDown(pressed)
            if pressed:
                button.pressed.emit()
            else:
                button.released.emit()
    
    
    # trackpad
    def handleCanvasCursorMoved(self, x, y):
        self.twistController.move(-y, -x * 2)