# -*- coding: utf-8 -*-
"""
Created on Sat Apr 14 23:11:00 2018

@author: Edward
"""

from __future__ import print_function

import numpy as np
import cv2
from commonFunctions import distance
from pointsManager import PointsManager
import pandas as pd

class MouseControl:
    def __init__(self, circlesMgr, circleDrawingMgr, shapeMgr):
        self.mode = 3
        self.buttonMode = 2 # polys
        
        self.flagEditingShape = False
        self.trackx = None
        self.tracky = None
        self.lButtonDown = False
        
        self.circlesMgr = circlesMgr
        self.circleDrawingMgr = circleDrawingMgr
        self.shapeMgr = shapeMgr
        
        self.updateScreenFlag = False
        self.flagEnableBorderWithShape = False      # Enable adding a border right after adding a new shape
        self.flagEnableAddingBorder = False         # Enable adding border to existing shapes
        self.flagSettingShapeBorder = False         # Are we setting the border of a shape now?
        
    def setMode(self, mode):
        self.mode = mode
        
    def setButtonMode(self, buttonMode):
        self.buttonMode = buttonMode
    
    """
        Returns True if the screen needs to be updated
    """
    def updateScreen(self):
        return self.updateScreenFlag
    
    """
        Are we editing a shape right now?
    """
    def setFlagEditingShape(self, flag):
        self.flagEditingShape = flag
        
    """
        Enable the functionality of adding a border to an existing shape.
    """
    def setFlagEnableAddingBorder(self, flagEnableAddingBorder):
        self.flagEnableAddingBorder = flagEnableAddingBorder
        
    """
        Enable the functionality of drawing a border right after
            adding a new shape.
    """
    def setFlagEnableBorderWithShape(self, flag):
        self.flagEnableBorderWithShape = flag
        
    """
        Are setting the border of a shape right now?
    """
    def setFlagSettingShapeBorder(self, flag, isAddingBorderToShape):
        if flag:
            if not isAddingBorderToShape and self.flagEnableBorderWithShape:
                self.flagSettingShapeBorder = True
            elif isAddingBorderToShape:
                self.flagSettingShapeBorder = True
        else:
            self.flagSettingShapeBorder = flag
            
        print('self.flagSettingShapeBorder: ',self.flagSettingShapeBorder)
        
    """
        Call this function to indicate you just updated the screen
    """
    def screenUpdated(self):
        self.updateScreenFlag = False
    
    def callback(self, event, x, y, flags, param):
        
        """
            Left mouse button click
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            """
                Is this inside a shape and are we in adding border mode?
            """
            flagDone = False
            if self.flagEnableAddingBorder and not self.flagSettingShapeBorder:
                flagDone = self.shapeMgr.addBorderToShape([y,x])
                if flagDone:
                    self.flagSettingShapeBorder = True
            
            if not flagDone:
                if self.flagSettingShapeBorder:
                    self.shapeMgr.addShapeBorder()
                    self.flagSettingShapeBorder = False
                    self.__setScreenUpdate()
                else:                
                    self.flagEditingShape = True
                    self.shapeMgr.addShapePoint([y,x])
                    self.__setScreenUpdate()
                
        elif event == cv2.EVENT_LBUTTONUP:
            pass
        
        elif event == cv2.EVENT_MOUSEMOVE:
            """
                Move the border
            """
            if self.flagSettingShapeBorder:
                self.shapeMgr.settingShapeBorderAtPoint([y,x])
                self.__setScreenUpdate()
        
        """
            Right mouse button click
        """
        if event == cv2.EVENT_RBUTTONDOWN:
            #print('EVENT_RBUTTONDOWN')
            if self.flagEditingShape:
                self.shapeMgr.removeShapePoint([y,x])
                if self.shapeMgr.isCurrentShapeEmpty():
                    """
                        Have we removed all the points of the current shape?
                        Then we are not in shape editing mode anymore!
                    """
                    self.flagEditingShape = False
            else:
                #print('removeShape')
                self.shapeMgr.removeShape(np.array([y,x]))
            self.__setScreenUpdate()
    
        elif event == cv2.EVENT_LBUTTONUP:
            pass
        
    """
        Sets the flag to indicate the screen needs updating
    """
    def __setScreenUpdate(self):
        self.updateScreenFlag = True
    