# -*- coding: utf-8 -*-
import os
from functools import partial
import math

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.phonon import Phonon

class RobotMediaPlayer():
    def __init__(self, ui, canvas):
        self.ui = ui
        self.canvas = canvas
        self.temporalization = None
        
        self.currentTimeToMaintain = 0
        
        self.currentVideoMediaSource = None
        self.currentMedia = None
        
        #TODO: conditions depending on the type of media
        self.videoPlayer = Phonon.VideoPlayer()
        self.ui.mediaContainer_widget.layout().addWidget(self.videoPlayer.videoWidget())
        self.videoPlayer.finished.connect(self.handleVideoPlayerFinished)
            
        self.ui.deleteMedia_button.setEnabled(False)
        
        self.mediaPlayingTimer = QTimer()
        self.mediaPlayingTimer.setInterval(1000. / 25)
        self.mediaPlayingTimer.timeout.connect(self.handleMediaPlaying)
        self.mediaPlayingTimer.start()
    
    
    def stop(self):
        self.videoPlayer.stop()
    
    
    def seek(self, value):
        self.currentTimeToMaintain = value
        self.videoPlayer.seek(self.currentTimeToMaintain)
    
    
    def currentTime(self):
        return self.videoPlayer.currentTime()
    
    
    def totalTime(self):
        return self.videoPlayer.totalTime()
    
    
    def setCurrentMedia(self, media):
        #TODO: conditions depending on the type of media
        if media is not None:
            self.currentVideoMediaSource = media.media
            self.currentMedia = media
            self.videoPlayer.load(media.media)
            self.videoPlayer.play()
            # if was playing, don't try to pause
            self.ui.deleteMedia_button.setEnabled(True)
            self.ui.media_groupBox.setTitle(u"Vidéo (" + os.path.basename(media.niceName).decode("utf-8") + u")")
        else:
            self.currentVideoMediaSource = None
            self.currentMedia = None
            self.ui.deleteMedia_button.setEnabled(False)
            self.ui.media_groupBox.setTitle(u"Vidéo")
        
        if self.temporalization is not None:
            self.temporalization.setTimelineValueCurrentMedia(0)
            
    
    def sendMediaToCanvas(self):
        #TODO: conditions depending on the type of media
        videoWidget = self.videoPlayer.videoWidget()
        videoWidgetAbsoluteCoords = videoWidget.mapToGlobal(QPoint(0, 0))
        snapshotRect = QRect(videoWidgetAbsoluteCoords.x(), videoWidgetAbsoluteCoords.y(), videoWidget.width(), videoWidget.height())
        snapshotPixmap = QPixmap.grabWindow(self.videoPlayer.winId(), snapshotRect.x(), snapshotRect.y(), snapshotRect.width(), snapshotRect.height())
        self.canvas.mediaPixmap = snapshotPixmap
        self.canvas.update()
        del snapshotPixmap
        
        
    def handleMediaPlaying(self):
        value = float(self.videoPlayer.currentTime()) / self.videoPlayer.totalTime()
        
        self.temporalization.setTimelineValueCurrentMedia(value)
        
        self.videoPlayer.pause()
        
        # fix a player bug which plays forever
        if not self.temporalization.isPlaying:
            self.videoPlayer.seek(self.currentTimeToMaintain)
        
        # update canvas
        self.sendMediaToCanvas()
        
    
    def handleVideoPlayerFinished(self):
        self.temporalization.playNextMedia()