# -*- coding: utf-8 -*-
"""
Created on Tue Jul 17 22:15:45 2018

@author: Edward
"""

import numpy as np

class ShapeData:
    def __init__(self, pointsManager):
        self.pointsManager = pointsManager
        self.XYWellNum = self.pointsManager.XYWellNum
        self.frameTotNum = self.pointsManager.frameTotNum
        
        self.shapesListFrames = []
        self.bordersListFrames = []
        self.shapesListFramesZ = []
        self.shapesListFramesID = []
        
        for i in range(self.XYWellNum):
            self.shapesListFrames.append([])
            self.bordersListFrames.append([])
            self.shapesListFramesZ.append([])
            self.shapesListFramesID.append([])
            for _ in range(self.frameTotNum):
                self.shapesListFrames[i].append([])
                self.bordersListFrames[i].append([])
                self.shapesListFramesZ[i].append([])
                self.shapesListFramesID[i].append([])
                
        self.coordinateFillerValue = -1  # The value given to a missing coordinate,
                                         # to fill up a square array from a non square array list.
        self.missingShapeBorder = []     # The value given to an entry when the data is missing
        self.missingShapeZValue = None   # The value given to an entry when the data is missing
        self.missingShapeIDValue = None  # The value given to an entry when the data is missing
        self.areaFillerValue = -1        # The value given to a missing area
        
    
    def loadDataFromFile(filename):
        pass
    
    def saveDataToFile(filename):
        pass
    
    def exportResultsToExcel(filename):
        pass
    
    def __updateCurrentFrame(self):
        self.currentXYWell = self.pointsManager.getCurrentXYWell()
        self.currentFrame = self.pointsManager.getCurrentFrame()
        
    """
        The shape points are stored as a floating point number
        to help converting between different screens. However, every time
        we read the points we need them as integers (pixels).
        
        Thus this function returns the shape points as integers.
        
        This returns all XY and all frames.
    """
    def getShapePointsRead(self):
        shapesListFrames = []
        for xy in range(len(self.shapesListFrames)):
            shapesListFrames.append([])
            for t in range(len(self.shapesListFrames[xy])):
                shapesListFrames[xy].append([])
                for shape in range(len(self.shapesListFrames[xy][t])):
                    shapesListFrames[xy][t].append([])
                    for point in range(len(self.shapesListFrames[xy][t][shape])):
                        shapesListFrames[xy][t][shape].append(np.array(self.shapesListFrames[xy][t][shape][point], dtype=int))
        return shapesListFrames
    
    """
        The shape points are stored as a floating point number
        to help converting between different screens. However, every time
        we read the points we need them as integers (pixels).
        
        Thus this function returns the shape points as integers.
        
        This returns only the current XY.
    """
    def getShapePointsCurrentXYRead(self):
        self.__updateCurrentFrame()
        
        xy = self.currentXYWell
        shapesListFramesCurrentXY = []
        for t in range(len(self.shapesListFrames[xy])):
            shapesListFramesCurrentXY.append([])
            for shape in range(len(self.shapesListFrames[xy][t])):
                shapesListFramesCurrentXY[t].append([])
                for point in range(len(self.shapesListFrames[xy][t][shape])):
                    shapesListFramesCurrentXY[t][shape].append(np.array(self.shapesListFrames[xy][t][shape][point], dtype=int))
        return shapesListFramesCurrentXY
    
    """
        The shape points are stored as a floating point number
        to help converting between different screens. However, every time
        we read the points we need them as integers (pixels).
        
        Thus this function returns the shape points as integers.
        
        This returns only the current frame in the current XY.
    """
    def getShapePointsCurrentXYFrameRead(self):
        self.__updateCurrentFrame()
        
        xy = self.currentXYWell
        t = self.currentFrame
        shapesListFramesCurrentXYFrame = []
        for shape in range(len(self.shapesListFrames[xy][t])):
            shapesListFramesCurrentXYFrame[t].append([])
            for point in range(len(self.shapesListFrames[xy][t][shape])):
                shapesListFramesCurrentXYFrame[t][shape].append(np.array(self.shapesListFrames[xy][t][shape][point], dtype=int))
        return shapesListFramesCurrentXYFrame