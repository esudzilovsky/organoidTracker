# -*- coding: utf-8 -*-
"""
Created on Sat Apr 14 20:34:29 2018

@author: Edward
"""

from __future__ import print_function

import numpy as np
from matplotlib import pyplot as plt
import cv2
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import os
import csv
from lineManager import lineMgr
from polygonShapeFinder import PolygonShapeFinder
from commonFunctions import distance, extendList, createFolder, anyNonEmpty
import pandas as pd
from natsort import natsorted
import sys
import ntpath
import trackpy
import itertools as IT
import globalSettings
import datetime
from messageBox import boolQuestionMBox
import copy
from expandPolygon import expandPolyUntillPoint
from expandCircle import expandCircleUntillPoint
from expandEllipse import expandEllipseUntillPoint
from equality import equal, all_equal, any_equal, not_equal, any_not_equal
from exportToUNet import exportToUNet
import json
from bson import json_util
#from shapeData import ShapeData

def drawCross(pic,x,y,rgb=(255,0,0),L=10):
    x = int(x)
    y = int(y)
    rgb = rgb[::-1]
    if isinstance(pic,list)==True:
        for k in pic:
            cv2.line(k,(y-L,x),(y+L,x),rgb)
            cv2.line(k,(y,x-L),(y,x+L),rgb)
    else:
        cv2.line(pic,(y-L,x),(y+L,x),rgb)
        cv2.line(pic,(y,x-L),(y,x+L),rgb)

def drawLine(pic,pt1,pt2,rgb=(255,255,255)):
    rgb = rgb[::-1]
    cv2.line(pic, (pt1[1],pt1[0]), (pt2[1],pt2[0]), rgb)
    
def drawRect(pic,x,y,rgb=(255,0,0),L=10):
    rgb = rgb[::-1]
    if isinstance(pic,list)==True:
        for k in pic:
            cv2.line(k,(y-L,x+L),(y+L,x+L),rgb)
            cv2.line(k,(y-L,x-L),(y+L,x-L),rgb)
            cv2.line(k,(y-L,x-L),(y-L,x+L),rgb)
            cv2.line(k,(y+L,x-L),(y+L,x+L),rgb)
    else:
        cv2.line(pic,(y-L,x+L),(y+L,x+L),rgb)
        cv2.line(pic,(y-L,x-L),(y+L,x-L),rgb)
        cv2.line(pic,(y-L,x-L),(y-L,x+L),rgb)
        cv2.line(pic,(y+L,x-L),(y+L,x+L),rgb)
        
def fitEllipse(points):    
    points = np.array(points, dtype=np.int64)
    (center, size, angle) = cv2.fitEllipse(np.array(points))
    return center, size, angle

def fitCircle(points):
    points = np.array(points, dtype=np.int64)
    center, radius = cv2.minEnclosingCircle(np.array(points))
    return center, radius
    
"""
    This class manager several point groups (shapes) in an image.
    
    The shapes data structure:
        self.shapesListFrames[xy_well][frame][shapeIndex][pointIndex] = (x,y)
        
        - There is an entry for every xy available in the video.
        - There is an entry for every frame of every xy available in the video.
        - The order of the shapes in every frame is meaningless.
        - There are no empty shapes ([])!
        - Every shape must have at least 3 points.
        - Every point is composed of 2 floating point coordinates, which must
          be non-negative.
        
        When saving to a file, this structure is converted to a square array
          meaning you must have the same number of shapes across all frames,
          and xy (the maximum number). And the number of points is also the
          max number for all shapes. Thus you add padded shapes and padded
          points. The point which is a padding is composed of 2 coordinates:
              self.coordinateFillerValue
              
    The borders data structure:
        self.bordersListFrames[xy_well][frame][borderIndex][pointIndex] = (x,y)
        
        - Has all the conditions imposed on the shapes structure.
        - Each border entry corresponds to an existing shape of the same index.
        - Thus, there must be an border entry for every existing shape entry.
        - If there is no border for a shape, it is equal to self.missingShapeBorder.
        
    The shape Z-level value data structure:
        self.shapesListFramesZ[xy_well][frame][shapeIndex] = frame z used for this shape
        
        - There is an entry for every xy available in the video.
        - There is an entry for every frame of every xy available in the video.
        - Each entry corresponds to an existing shape of the same index.
        - Thus, there must be Z-level entry for every existing shape entry.
        - If there is no Z-level for a shape, it is equal to self.missingShapeZValue.
        
        When saving to a file this structure is converted to a square array,
            such that the number of shapes is uniform across different frames
            and xy. It is thus padded with special Z values (self.coordinateFillerValue).
            Missing Z is also written as self.coordinateFillerValue.
        
    The shape ID data structure:
        self.shapesListFramesID[xy_well][frame][shapeIndex] = shape ID
        
        - There is an entry for every xy available in the video.
        - There is an entry for every frame of every xy available in the video.
        - Each entry corresponds to an existing shape of the same index.
        - Thus, there must be ID entry for every existing shape entry.
        - If there is no ID for a shape, it is equal to self.missingShapeIDValue.
    
        When saving to a file this structure is converted to a square array,
            such that the number of shapes is uniform across different frames
            and xy. It is thus padded with special ID values (self.coordinateFillerValue).
            Missing ID is also written as self.coordinateFillerValue.
"""
class PointsManager:
    """
        screenFactor - the factor that the original width / height of the video
                        was multiplied by to make it fit the window size wanted.
    """
    def __init__(self, frameCtrl):#XYWellNum, frameTotNum, currentFrame, currentXYWell, screenFactor):
        print('   --- Intializing PointsManager ---')
        self.saveDir = frameCtrl.getVideoPath() + frameCtrl.getVideoBasename() + '_tracking/'
        
        #self.shapeData = ShapeData(self)
        
        """
            This is the version of the organoidTracker
        """
        self.organoidTrackerVersion = globalSettings.getOrganoidTrackerVersion()
        
        """
            This is the directory where backups are saved
        """
        self.trackingDirectory = None
        
        self.XYWellNum = frameCtrl.getXYWellCount()
        self.frameTotNum = frameCtrl.getFrameCount()
        print('   XYWellNum = '+np.str(self.XYWellNum))
        print('   frameTotNum = '+np.str(self.frameTotNum))
        """
            This is a list:
                self.shapesListFrames[xy_well][frame][shapeIndex][pointIndex] = (x,y)
        """
        self.shapesListFrames = []
        self.coordinateFillerValue = -1 # The value given to a missing coordinate,
                                        # to fill up a square array from a non square array list.
        """
            The borders for the shapes.
            This is a list:
                self.bordersListFrames[xy_well][frame][borderIndex][pointIndex] = (x,y)
        """
        self.bordersListFrames = []
        self.missingShapeBorder = []    # The value given to an entry when the data is missing
        """
            This is a list:
                self.shapesListFramesZ[xy_well][frame][shapeIndex] = frame z used for this shape
        """
        self.shapesListFramesZ = []
        self.missingShapeZValue = None  # The value given to an entry when the data is missing
        """
            This is a list:
                self.shapesListFramesID[xy_well][frame][shapeIndex] = shape ID
        """
        self.shapesListFramesID = []
        self.missingShapeIDValue = None  # The value given to an entry when the data is missing
        
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
                
        self.areaFillerValue = -1        # The value given to a missing area
            
        self.currentFrame = frameCtrl.getCurrentFrameNumber()
        self.lastBackupFrame = self.currentFrame
        #print('pointsMgr.currentFrame: '+np.str(self.currentFrame))
        self.currentXYWell = frameCtrl.getCurrentXYWellNumber()
        self.screenFactor = frameCtrl.getScreenFactor()
        self.frameCtrl = frameCtrl
        
        #self.shapesList = []
        self.gDataDir = None
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.shapePoints = []
        self.borderPoints = []
        self.polyMaskList = []
        self.polyMaskPointsList = []
        self.polyIntensities = []
        
        #self.shapeRGB = np.array((65,105,225),dtype=int)         # Color of the shape
        self.shapeRGB = np.array((51,255,255), dtype=int)
        self.borderRGBBuilding = np.array((128,255,0), dtype=int)
        self.borderRGBComplete = np.array((255,165,0), dtype=int)
        self.shapeIndexBeingAddedBorder = None  # The shape index of the shape we are adding a border to
        
        self.prevFrame = None               # The previous frame where we showed stuff
        self.showShapesFromPrevFrame = None # The previous frame to show shapes from
        self.shapeCrossRGB = (243,243,21)   # Color of the crosshair
        self.frameSkip = None               # # of frames to skip between showing of frames
        self.umpixel = None                 # um/pixel ratio 
        self.updateScreenFlag = False       # Does the screen need to be updated?
        
        """
            The last removal action data, 
            this is required for the undo
            functionality
        """
        self.lastRemovalAction = None       # 'point' | 'shape' -- this indicates the last thing that was removed
        self.lastPointRemoved = None        # the actual last point that was removed
        self.lastShapeRemoved = None        # the actual last shape data that was removed
        
        """
            Editing the points manually
        """
        self.preEditCurrentXYPointsStored = False      # Are the pre-edit points stored?
                                                       # (have we started an edit but not finilized it)?
        self.preEditCurrentXYPoints = None             # The pre-edit points
    
        print('   ---  PointsManager Initialized ! ---')
        
    """
        The shape points are stored as a floating point number
        to help converting between different screens. However, every time
        we read the points we need them as integers (pixels).
        
        Thus this function returns the shape points as integers.
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
                        #shapesListFrames[xy][t][shape].append([])
                        #for coordinate in self.shapesListFrames[xy][t][shape][point]:
                        #    shapesListFrames[xy][t][shape][point].append(int(coordinate))
        return shapesListFrames
    
    def getBorderPointsRead(self):
        bordersListFrames = []
        for xy in range(len(self.bordersListFrames)):
            bordersListFrames.append([])
            for t in range(len(self.bordersListFrames[xy])):
                bordersListFrames[xy].append([])
                for shape in range(len(self.bordersListFrames[xy][t])):
                    bordersListFrames[xy][t].append([])
                    for point in range(len(self.bordersListFrames[xy][t][shape])):
                        bordersListFrames[xy][t][shape].append(np.array(self.bordersListFrames[xy][t][shape][point], dtype=int))
    
        return bordersListFrames
    
    """
        The shape points are stored as a floating point number
        to help converting between different screens. However, every time
        we read the points we need them as integers (pixels).
        
        Thus this function returns the shape points as integers.
    """
    def getShapePointsCurrentXYRead(self):
        xy = self.currentXYWell
        shapesListFramesCurrentXY = []
        for t in range(len(self.shapesListFrames[xy])):
            shapesListFramesCurrentXY.append([])
            for shape in range(len(self.shapesListFrames[xy][t])):
                shapesListFramesCurrentXY[t].append([])
                for point in range(len(self.shapesListFrames[xy][t][shape])):
                    shapesListFramesCurrentXY[t][shape].append(np.array(self.shapesListFrames[xy][t][shape][point], dtype=int))
        return shapesListFramesCurrentXY
    
    def getBorderPointsCurrentXYRead(self):
        xy = self.currentXYWell
        bordersListFramesCurrentXY = []
        for t in range(len(self.bordersListFrames[xy])):
            bordersListFramesCurrentXY.append([])
            for border in range(len(self.bordersListFrames[xy][t])):
                bordersListFramesCurrentXY[t].append([])
                for point in range(len(self.bordersListFrames[xy][t][border])):
                    bordersListFramesCurrentXY[t][border].append(np.array(self.bordersListFrames[xy][t][border][point], dtype=int))
        return bordersListFramesCurrentXY
    
    """
        The shape points are stored as a floating point number
        to help converting between different screens. However, every time
        we read the points we need them as integers (pixels).
        
        Thus this function returns the shape points as floats.
    """
    def getShapePointsWrite(self):
        return self.shapesListFrames
    
    def getBorderPointsWrite(self):
        return self.bordersListFrames
    
    """
        The shape points are stored as a floating point number
        to help converting between different screens. However, every time
        we read the points we need them as integers (pixels).
        
        Thus this function returns the shape points as floats.
    """
    def getShapePointsCurrentXYWrite(self):
        xy = self.currentXYWell
        return self.shapesListFrames[xy]
    
    def getBorderPointsCurrentXYWrite(self):
        xy = self.currentXYWell
        return self.bordersListFrames[xy]
    
    """
        Are the pre-edit points stored already (have we done an
        edit but not finilized it)?
    """
    def __preEditCurrentXYPointsStored(self):
        return self.preEditCurrentXYPointsStored
    
    """
        Stores all the current XY points, before making a change to them.
    """
    def __storePreEditCurrentXYPoints(self):
        shapePointsCurrentXYWrite = self.getShapePointsCurrentXYWrite()
        self.preEditCurrentXYPoints = copy.deepcopy(shapePointsCurrentXYWrite)
        self.preEditCurrentXYPointsStored = True
        
    """
        Finalize the most recent edit
    """
    def finalizeMostRecentEdit(self):
        self.preEditCurrentXYPointsStored = False
        self.preEditCurrentXYPoints = None
    
    """
        Restore the points as they were previous to any recent edits.
    """
    def __restorePreEditCurrentXYPoints(self):
        shapePointsCurrentXYWrite = self.getShapePointsCurrentXYWrite()
        for t in range(len(shapePointsCurrentXYWrite)):
            shapePointsCurrentXYWrite[t] = copy.deepcopy(self.preEditCurrentXYPoints[t])
    
    """
        Edits the points between the two frames (included).
        The points are shifted in x by xFactor and in y by yFactor.
    """
    def editPointsShift(self, firstFrameEdit, lastFrameEdit, xFactor, yFactor):
        """
            Store the current XY points before any editing.
            If this is an additional edit, restore the pre-edit points.
        """
        if not self.__preEditCurrentXYPointsStored():
            self.__storePreEditCurrentXYPoints()
        else:
            self.__restorePreEditCurrentXYPoints()
            
        factor = np.array([xFactor,yFactor],dtype=np.float64)
        shapePointsCurrentXYWrite = self.getShapePointsCurrentXYWrite()
        
        for t in range(firstFrameEdit, lastFrameEdit+1):
            for shapeIndex in range(len(shapePointsCurrentXYWrite[t])):
                for point in range(len(shapePointsCurrentXYWrite[t][shapeIndex])):
                    shapePointsCurrentXYWrite[t][shapeIndex][point] = np.array(shapePointsCurrentXYWrite[t][shapeIndex][point],dtype=np.float64)+factor
    
    """
        Edits the points between the two frames (included).
        The points are multiplied in x by xFactor and in y by yFactor.
    """
    def editPointsMultiply(self, firstFrameEdit, lastFrameEdit, xFactor, yFactor):
        """
            Store the current XY points before any editing.
            If this is an additional edit, restore the pre-edit points.
        """
        if not self.__preEditCurrentXYPointsStored():
            self.__storePreEditCurrentXYPoints()
        else:
            self.__restorePreEditCurrentXYPoints()
            
        factor = np.array([xFactor,yFactor],dtype=np.float64)
        shapePointsCurrentXYWrite = self.getShapePointsCurrentXYWrite()
        
        for t in range(firstFrameEdit, lastFrameEdit+1):
            for shapeIndex in range(len(shapePointsCurrentXYWrite[t])):
                for point in range(len(shapePointsCurrentXYWrite[t][shapeIndex])):
                    shapePointsCurrentXYWrite[t][shapeIndex][point] = np.array(shapePointsCurrentXYWrite[t][shapeIndex][point],dtype=np.float64)
                    shapePointsCurrentXYWrite[t][shapeIndex][point][0] *= factor[0]
                    shapePointsCurrentXYWrite[t][shapeIndex][point][1] *= factor[1]
        
    """
        Sets how many um per pixel
    """
    def setUmPixel(self, umpixel):
        self.umpixel = np.float64(umpixel)
        
    """
        Does the screen need to be updated?
    """
    def updateScreen(self):
        return self.updateScreenFlag
    
    """
        Call this function to indicate you just updated the screen
    """
    def screenUpdated(self):
        self.updateScreenFlag = False
        
    """
        This function changes the ids (order of shapes) across frames
        by finding matching shape centers.
    """
    def trackShapes(self):
        DEBUG = False
        shapePointsCurrentXYRead = self.getShapePointsCurrentXYRead()
        
        x,y = [],[]
        frame = []
        i = 0
        if DEBUG:
            print('\ti\tframe\tx\ty')
        for t in range(self.frameTotNum):
            if len(shapePointsCurrentXYRead[t])==0:
                continue
            for shapeIndex in range(len(shapePointsCurrentXYRead[t])):
                center = self.__getShapeCenter(shapePointsCurrentXYRead[t][shapeIndex])
                x.append(center[0])
                y.append(center[1])
                frame.append(t)
                if DEBUG:
                    if False:
                        if t==35 or t==40:
                            print(np.str(i)+'\t'+np.str(t)+'\t'+np.str(np.round(center[0]))+'\t'+np.str(np.round(center[1])))
                i += 1
        
        """
            features : DataFrame
                Must include any number of column(s) for position and a column of
                frame numbers. By default, ‘x’ and ‘y’ are expected for position,
                and ‘frame’ is expected for frame number. See below for options to
                use custom column names. After linking, this DataFrame will contain
                a ‘particle’ column.
        """
        data = {'frame':np.array(frame,dtype=int),'x':np.array(x),'y':np.array(y)}
        featuresDF = pd.DataFrame(data)
        """
            search_range : float
                the maximum distance features can move between frames
        """
        areas = self.__getShapeAreas()
        search_range = int(np.sqrt(np.max(areas))/np.pi)#150
        """
            memory : integer
                the maximum number of frames during which a feature can vanish,
                then reppear nearby, and be considered the same particle. 0 by default.
        """
        memory = (2+1)*self.frameCtrl.getFrameSkip() + 1
        
        """
            Returns:	
                trajectories : DataFrame
                    This is the input features DataFrame, now with a new column labeling
                    each particle with an ID number. This is not a copy; the original features
                    DataFrame is modified.
        """
        trajectoriesDF = trackpy.link_df(featuresDF, search_range, pos_columns=['x','y'], memory=memory)
        
        print("Tracking results...")
        if DEBUG:
            print(trajectoriesDF)
        
        if DEBUG:
            if False:
                print('trajectoriesDF frames 34 and 35:')
                #for i in range(len(trajectoriesDF)):
                rowiter = trajectoriesDF.iterrows()
                for i in range(100):
                    index, row = next(rowiter)
                    if row['frame']==40 or row['frame']==35:
                        print(row)
                
        rowiter = trajectoriesDF.iterrows()
        """
        for t in range(self.frameTotNum):
            if len(shapePointsCurrentXYRead[t])==0:
                continue
            
            for shapeIndex in range(len(shapePointsCurrentXYRead[t])):
                index, row = next(rowiter)
                #frame = row['frame']
                ID = row['particle']
            
                # Find that shape
                #for shapeIndex in self
                
                #if int(t)==40:
                #    print('DEBUG: SET shape index: ',shapeIndex,' to ID '+ID)
                print('   DEBUG: SET frame: '+np.str(t)+' shape index: ',shapeIndex,' to ID '+np.str(np.int(ID)))
            
                self.shapesListFramesID[self.currentXYWell][t][shapeIndex] = np.int(ID)
            """
            
        """
            Note: for some reason the order of the output changes from the input order
            so you need to match (x,y) pairs
        """

        try:            
            while True:
                index, row = next(rowiter)
                
                shapes = shapePointsCurrentXYRead[int(row['frame'])]
                
                foundFlag = False
                for shapeIndex in range(len(shapes)):
                    center = self.__getShapeCenter(shapes[shapeIndex])
                    if center[0]==row['x'] and center[1]==row['y']:
                        self.shapesListFramesID[self.currentXYWell][int(row['frame'])][shapeIndex] = int(row['particle'])
                        foundFlag = True
                        break
                if not foundFlag:
                    print('Error! particle not matched after tracking!')
        except StopIteration:
            pass
        
        return
        prevCenters = []
        for t in range(self.frameTotNum):
            centers = []
            for shapeIndex in range(len(shapePointsCurrentXYRead[t])):
                centers.append(self.__getShapeCenter(shapePointsCurrentXYRead[t][shapeIndex]))
            
            # If this is the first frame where the organoids appear skip it
            if len(prevCenters)==0:
                continue
            
            matchedIndexes = [] # Matched indexs in (prevCenters, centers)
            for i in range(len(prevCenters)):
                prevCenter = prevCenters[i]
                distances = np.array([distance(prevCenter,pt) for pt in centers])
                indexMinDistance = np.argmin(distances)
                matchedIndexes.append(i, indexMinDistance)
                
            """
                Are there any double matches?
            """
            matchedPrevIndexes = [match[0] for match in matchedIndexes]
            matchedIndexes = [match[1] for match in matchedIndexes]
            matchedPrevIndexesUnique = np.unique(matchedPrevIndexes)
            matchedIndexesUnique = np.unique(matchedIndexes)
            
            processedMatches = []
            for match in matchedIndexes:
                prevCenterIndex = match[0]
                centerIndex = match[1]
                
                if prevCenterIndex in matchedPrevIndexesUnique and centerIndex in matchedIndexesUnique:
                    processedMatches.append(match)
                elif prevCenterIndex not in matchedPrevIndexesUnique \
                    and centerIndex not in matchedIndexesUnique:
                        pass
    
    """
        Returns all the shapes in all xy, frames.
    """
    def __getShapesSortedByID(self, dtype=np.int64):
        shapePointsWrite = self.getShapePointsWrite()
        
        shapesDict = dict()
        for xy in range(len(shapePointsWrite)):
            for t in range(len(shapePointsWrite[xy])):
                for shapeIndex in range(len(shapePointsWrite[xy][t])):
                    shapeID = self.shapesListFramesID[xy][t][shapeIndex]
                    shapesDict[(xy,t,shapeID)] = np.array(shapePointsWrite[xy][t][shapeIndex], dtype=dtype)
        shapes = []
        for (xy,t,shapeID) in shapesDict.keys():
            shapes = extendList(shapes, xy, t, shapeID)
            shapes[xy][t][shapeID] = shapesDict[(xy,t,shapeID)]
        return shapes
    
    def __getShapeCenter(self, points):
        shapeType = self.shapeType(points)
        if shapeType=='circle':
            center, radius = fitCircle(points)
        elif shapeType=='ellipse':
            center, size ,angle = fitEllipse(points)
        elif shapeType=='points':
            center = np.mean(points,1)
        elif shapeType=='polygon':
            center = self.__getPolygonCenter(points)#np.mean(points,1)
        return center
    
    """
        Careful - this may not work for polygons that intersect themselves!
    """
    def __getPolygonCenter(self, points):
        #print('__getPolygonCenter')
        """
        http://stackoverflow.com/a/14115494/190597 (mgamba)
        """
        """
        
        # THIS CODE DOESN'T WORK!!!
        
        area = self.__getPolygonArea(points)
        result_x = 0
        result_y = 0
        N = len(points)
        points = IT.cycle(points)
        x1, y1 = next(points)
        for i in range(N):
            x0, y0 = x1, y1
            x1, y1 = next(points)
            cross = (x0 * y1) - (x1 * y0)
            result_x += (x0 + x1) * cross
            result_y += (y0 + y1) * cross
        result_x /= (area * 6.0)
        result_y /= (area * 6.0)
        return (result_x, result_y)
        """
        
        # https://stackoverflow.com/questions/2792443/finding-the-centroid-of-a-polygon
        
        centeroid = np.array((0,0), dtype=np.float64)
        signedArea, x0, y0, x1, y1, a = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        
        for i in range(len(points)):
            x0 = points[i][0]
            y0 = points[i][1]
            x1 = points[(i+1) % len(points)][0]
            y1 = points[(i+1) % len(points)][1]
            a = x0*y1 - x1*y0
            signedArea += a
            centeroid[0] += (x0 + x1)*a
            centeroid[1] += (y0 + y1)*a
            
        signedArea *= 0.5 # This area may be negative!        
        return np.array(centeroid / (6.0*signedArea), dtype=np.int64)
    
    def __expandPoly(self, points, factor):
        points = np.array(points, dtype=np.float64)
        expandedPoly = points*factor
        expandedPoly -= self.__getPolyCenter(expandedPoly)
        expandedPoly += self.__getPolyCenter(points)
        return np.array(expandedPoly, dtype=np.int64)
    
    def getCurrentFrame(self):
        return self.currentFrame
    
    def getCurrentXYWell(self):
        return self.currentXYWell
    
    """
        Set the border of the last added shape
    """
    def settingShapeBorderAtPoint(self, point):
        shapePointsCurrentXYFrameRead = self.getShapePointsCurrentXYRead()[self.currentFrame]
        if self.shapeIndexBeingAddedBorder is None:
            self.shapeIndexBeingAddedBorder = len(shapePointsCurrentXYFrameRead)-1
        
        shapePoints = shapePointsCurrentXYFrameRead[self.shapeIndexBeingAddedBorder]
        shapeType = self.shapeType(shapePoints)
        if shapeType=='circle':
            self.borderPoints = copy.deepcopy(expandCircleUntillPoint(shapePoints, point))
        elif shapeType=='ellipse':
            self.borderPoints = copy.deepcopy(expandEllipseUntillPoint(shapePoints, point))
        elif shapeType=='polygon':
            self.borderPoints = copy.deepcopy(expandPolyUntillPoint(shapePoints, point))
        else:
            self.borderPoints = []
            return
    
    """
        Add the border for the last shape
    """
    def addShapeBorder(self, borderPoints = None):
        if borderPoints is None:
            borderPoints = self.borderPoints
        
        shapePointsCurrentXYFrameRead = self.getShapePointsCurrentXYRead()[self.currentFrame]
        if self.shapeIndexBeingAddedBorder is None:
            self.shapeIndexBeingAddedBorder = len(shapePointsCurrentXYFrameRead)-1
            
        borderPointsCurrentXYFrameWrite = self.getBorderPointsCurrentXYWrite()[self.currentFrame]
        borderPointsCurrentXYFrameWrite = extendList(borderPointsCurrentXYFrameWrite, self.shapeIndexBeingAddedBorder)
        borderPointsCurrentXYFrameWrite[self.shapeIndexBeingAddedBorder] = copy.deepcopy(borderPoints)
            
        # Clear current burder points
        self.borderPoints = []
        
        # Reset
        self.shapeIndexBeingAddedBorder = None
        
    """
        Finish the last shape with no border
    """
    def finishShapeNoBorder(self):      
        shapePointsCurrentXYFrameRead = self.getShapePointsCurrentXYRead()[self.currentFrame]
        #shapePoints = shapePointsCurrentXYFrameRead[-1]
        #borderPoints = expandPolyUntillPoint(shapePoints, point)
        borderPointsCurrentXYFrameWrite = self.getBorderPointsCurrentXYWrite()[self.currentFrame]
        if len(borderPointsCurrentXYFrameWrite)>len(shapePointsCurrentXYFrameRead):
            borderPointsCurrentXYFrameWrite[len(shapePointsCurrentXYFrameRead)-1] = []
        else:
            borderPointsCurrentXYFrameWrite.append([])
            
        # Clear current burder points
        self.borderPoints = []
        
    
    def isFrameNotEmpty(self, frameIndex):
        shapePointsCurrentXYWrite = self.getShapePointsCurrentXYWrite()
        #out = len(shapePointsCurrentXYWrite[frameIndex])>0
        out = anyNonEmpty(shapePointsCurrentXYWrite[frameIndex])
        #print('---- isFrameNotEmpty('+str(frameIndex)+') = '+str(out))
        return out
        
    def setCurrentFrame(self, currentFrame):
        #print('setCurrentFrame: ',currentFrame)
        #print(' - cur frame: ',self.currentFrame)
        #print(' - prev frame: ',self.prevFrame)
        shapePointsCurrentXYWrite = self.getShapePointsCurrentXYWrite()
        
        if self.prevFrame is not None:
            if self.prevFrame==currentFrame:
                pass
            elif self.prevFrame!=currentFrame:
                """
                    We want to show shapes from the last frame
                    that had shapes in it. Not necessarily the previous
                    frame, which may not have shapes.
                """
                if self.isFrameNotEmpty(self.prevFrame):
                    #print('self.isFrameNotEmpty(self.prevFrame) = ',self.isFrameNotEmpty(self.prevFrame))
                    #print('setting self.showShapesFromPrevFrame')
                    self.showShapesFromPrevFrame = copy.deepcopy(self.prevFrame)
            #self.currentFrame = currentFrame
            #self.prevFrame = currentFrame
        #else:
            #self.currentFrame = currentFrame
            #self.prevFrame = currentFrame
        self.prevFrame = copy.deepcopy(currentFrame)
        self.currentFrame = copy.deepcopy(currentFrame)
            
        """
            If the distance from this frame to the last saved frame is 50 frames or more
            OR at least 10 new frames have shapes in them, save data to backup
        """
        minFrame = np.min([currentFrame, self.lastBackupFrame+1])
        maxFrame = np.min([currentFrame, self.lastBackupFrame-1])
        newFrames = np.array(list(range(minFrame, maxFrame+1, 1)),dtype=int)
        
        """
            Count number of new frames with at least one shape in the frame
        """
        newFramesWithShapes = 0
        for t in newFrames:
            if len(shapePointsCurrentXYWrite[t])>0:
                newFramesWithShapes += 1
        
        if np.abs(currentFrame-self.lastBackupFrame)>=5 or newFramesWithShapes>=3:
            self.saveDataBackup()
        #if np.abs(currentFrame-self.lastBackupFrame)>=10 or newFramesWithShapes>=2:
            #self.saveDataBackup()
            
    """
        The directory you set with this right now is only used for backups
    """
    def setTrackingDirectory(self, trackDir):
        self.trackingDirectory = trackDir
        
    """
        Save a backup shapes file
    """
    def saveDataBackup(self):
        print('Saving backup...')
        try:
            self.saveShapes(self.trackingDirectory + 'shapes.backup')
        except Exception as e:
            print('Could not save backup!')
            globalSettings.logError()
            return False
        
        """
            The last backup frame becomes the current frame!
        """
        self.lastBackupFrame = self.currentFrame
        return True
    
    def removeBackup(self):
        try:
            os.remove(self.trackingDirectory + 'shapes.backup.npy')
            return True
        except Exception as e:
            globalSettings.logError()
            return False
    
    """
        Load from a backup file
    """
    def loadBackup(self):
        print('Loading from backup...')
        try:
            self.loadShapes(self.trackingDirectory, self.trackingDirectory + 'shapes.backup.npy')
        except Exception as e:
            print('Could not load backup!')
            globalSettings.logError()
            return False
        return True
        
    def getCurrentFrame(self):
        return self.currentFrame
    
    def __addShape(self, points, zIndex):
        shapePointsCurrentXYWrite = self.getShapePointsCurrentXYWrite()
        
        #print('Adding shape @ frame: '+np.str(self.currentFrame))
        shapePointsCurrentXYWrite[self.currentFrame].append(points)
        self.shapesListFramesZ[self.currentXYWell][self.currentFrame].append(zIndex)
        if anyNonEmpty(self.shapesListFramesID[self.currentXYWell]):
            indexes = []
            for t in range(len(self.shapesListFramesID[self.currentXYWell])):
                for shapeID in range(len(self.shapesListFramesID[self.currentXYWell][t])):
                    index = self.shapesListFramesID[self.currentXYWell][t][shapeID]
                    if not_equal(index, self.missingShapeIDValue):
                        indexes.append(index)
            
            if len(indexes)==0:
                index = 0
            else:
                index = np.max(indexes)+1
            
            self.shapesListFramesID[self.currentXYWell][self.currentFrame].append(index)
        else:
            self.shapesListFramesID[self.currentXYWell][self.currentFrame].append(0)
    
    """
    def __removeLastShape(self):
        shapePointsCurrentXYWrite = self.getShapePointsCurrentXYWrite()
        
        if len(shapePointsCurrentXYWrite[self.currentFrame])>0:
            del shapePointsCurrentXYWrite[self.currentFrame][-1]
            del self.shapesListFramesZ[self.currentXYWell][self.currentFrame][-1]
            del self.shapesListFramesID[self.currentXYWell][self.currentFrame][-1]
    """
    #def getCurrentShapesList(self):
    #    return self.shapesListFrames[self.currentFrame]
    
    """
        Set the z stack for this shape in this frame
    """
    def setShapeZStack(self, frame, shapeIndex, z):
        self.shapesListFramesZ[self.currentXYWell] = extendList(self.shapesListFramesZ[self.currentXYWell], frame, shapeIndex)
        self.shapesListFramesZ[self.currentXYWell][frame][shapeIndex] = z
        
    def shapeType(self, points):
        if len(points)<3:
            return 'points'
        elif len(points)<5:
            return 'circle'
        elif len(points)<9:
            return 'ellipse'
        else:
            return 'polygon'
    
    def addShapePoint(self, point):
        self.shapePoints.append(np.array(point,dtype=int))
        
    def removeShapePoint(self, location):
        for i in range(0,len(self.shapePoints)):
            if i>=len(self.shapePoints):
                break
            if distance(self.shapePoints[i],location)<=10:
                self.lastRemovalAction = 'point'
                self.lastPointRemoved = self.shapePoints[i]
                del self.shapePoints[i]
        pass
        
    def clearCurrentShape(self):
        self.shapePoints = []
        
    """
        Close the polygon by making the first point also the last point
    """
    def closePoly(self):
        if len(self.shapePoints)>1:
            self.addShapePoint(self.shapePoints[0])
            
    """
        Returns the polygon the user is working on right now
    """
    def getCurrentShape(self):
        return self.shapePoints
    
    """
        Is the current shape empty?
    """
    def isCurrentShapeEmpty(self):
        return len(self.shapePoints)==0

    def addShape(self, points, zIndex):
        if self.shapeType(points)=='points':
            print('Cannot add shape: not enough points!')
            return
        
        if self.shapeType(points)=='polygon':
            """
                Make sure the points are in the correct order before saving
            """
            polyFinder = PolygonShapeFinder(points)
            points = polyFinder.getSortedPolygon()
        self.__addShape(points, zIndex)
        
    """
        Remove the last (added) polygon
    """
    #def removeLastShape(self):
    #    self.__removeLastShape()
        
    """
        Block undo operations on stuff already done.
        boolAllUndos - if True, then all undo, if False only point undo are blocked.
    """
    def blockUndoOperation(self, boolAllUndos):
        if boolAllUndos:
            self.lastRemovalAction = None
            self.lastPointRemoved = None
            self.lastShapeRemoved = None
        else:
            if self.lastRemovalAction=='point':
                self.lastRemovalAction = None
                self.lastPointRemoved = None
        
    """
        Undo the last removal operation
    """
    def undoLastRemoval(self):
        """
            Undo the last removal operation
        """
        if self.lastRemovalAction=='point':
            self.addShapePoint(self.lastPointRemoved)
        elif self.lastRemovalAction=='shape':
            self.addShape(self.lastShapeRemoved[0], self.lastShapeRemoved[2])
            self.addShapeBorder(self.lastShapeRemoved[3])
        
        """
            Block further 'undo' operations
        """
        self.blockUndoOperation(True)
        
        """
            We need to update the screen
        """
        self.updateScreenFlag = True
        
    """
        If the point is inside an exisitng shape, start adding a border to
        the shape
    """
    def addBorderToShape(self, point):
        shapePointsCurrentXYRead = self.getShapePointsCurrentXYRead()
        shapePointsCurrentXYWrite = self.getShapePointsCurrentXYWrite()
        borderPointsCurrentXYWrite = self.getBorderPointsCurrentXYWrite()
        shapes = shapePointsCurrentXYRead[self.currentFrame]
        
        """
            Find all the shapes the point falls inside of
        """
        shapeIndexes = []
        shapeCenterDistance = []
        for i in range(len(shapes)):
            shapePoints = shapes[i]
            #print('__pointInsideShape(',i,')...')
            if self.__pointInsideShape(shapePoints, point):
                shapeIndexes.append(i)
                shapeCenterDistance.append(distance(point,self.__getShapeCenter(shapePoints)))
        
        """
            Find the shape the center of which is closest to the point
        """
        if len(shapeCenterDistance)>0:
            minIndex = np.argmin(shapeCenterDistance)
            shapeIndex = shapeIndexes[minIndex]
            
            """
                Does this shape already have a border?
            """
            if anyNonEmpty(borderPointsCurrentXYWrite[self.currentFrame][shapeIndex]):
                return False
            
            self.shapeIndexBeingAddedBorder = shapeIndex
            return True
        
        return False
        
    """
        Finds the shapes that the point is inside of, of those it will
        remove the shape that the point is closest to its center.
    """
    def removeShape(self, point):
        #print('removeShape()')
        shapePointsCurrentXYRead = self.getShapePointsCurrentXYRead()
        shapePointsCurrentXYWrite = self.getShapePointsCurrentXYWrite()
        #borderPointsCurrentXYRead = self.getBorderPointsCurrentXYRead()
        borderPointsCurrentXYWrite = self.getBorderPointsCurrentXYWrite()
        shapes = shapePointsCurrentXYRead[self.currentFrame]
        
        """
            Find all the shapes the point falls inside of
        """
        shapeIndexes = []
        shapeCenterDistance = []
        for i in range(len(shapes)):
            shapePoints = shapes[i]
            #print('__pointInsideShape(',i,')...')
            if self.__pointInsideShape(shapePoints, point):
                shapeIndexes.append(i)
                shapeCenterDistance.append(distance(point,self.__getShapeCenter(shapePoints)))
        
        """
            Find the shape the center of which is closest to the point
        """
        if len(shapeCenterDistance)>0:
            minIndex = np.argmin(shapeCenterDistance)
            shapeIndex = shapeIndexes[minIndex]
            #print('Shape to be removed: ',shapeIndex)
            
            self.lastRemovalAction = 'shape'
            self.lastShapeRemoved = [shapePointsCurrentXYWrite[self.currentFrame][shapeIndex]
                                    ,self.shapesListFramesID[self.currentXYWell][self.currentFrame][shapeIndex]
                                    ,self.shapesListFramesZ[self.currentXYWell][self.currentFrame][shapeIndex]
                                    ,borderPointsCurrentXYWrite[self.currentFrame][shapeIndex]]
            
            """
                Remove the shape from all frames!
            """
            """
            for t_ in range(len(shapePointsCurrentXYWrite)):
                del shapePointsCurrentXYWrite[t_][shapeIndex]
                del borderPointsCurrentXYWrite[t_][shapeIndex]
                del self.shapesListFramesID[self.currentXYWell][t_][shapeIndex]
                del self.shapesListFramesZ[self.currentXYWell][t_][shapeIndex]
            """
            del shapePointsCurrentXYWrite[self.currentFrame][shapeIndex]
            del borderPointsCurrentXYWrite[self.currentFrame][shapeIndex]
            del self.shapesListFramesID[self.currentXYWell][self.currentFrame][shapeIndex]
            del self.shapesListFramesZ[self.currentXYWell][self.currentFrame][shapeIndex]
            
    """
        Is the point inside the shape?
    """
    def __pointInsideShape(self, shapePoints, point):
        shapeType = self.shapeType(shapePoints)
        if shapeType=='points':
            return False
        elif shapeType=='polygon':
            return self.__pointInsidePolygon(shapePoints, point)
        elif shapeType=='circle':
            return self.__pointInsideCircle(shapePoints, point)
        elif shapeType=='ellipse':
            return self.__pointInsideEllipse(shapePoints, point)
        
    """
        Is the point inside the polygon?
    """
    def __pointInsidePolygon(self, shapePoints, point):
        polygon = Polygon(shapePoints);
        return polygon.contains(Point(point[0],point[1]))
    
    """
        Is the point inside the circle fit for these shapePoints?
    """
    def __pointInsideCircle(self, shapePoints, point):
        center, radius = fitCircle(shapePoints)
        return distance(center, point)<=radius
    
    """
        Is the point inside the ellipse fit for these shapePoints?
    """
    def __pointInsideEllipse(self, shapePoints, point):
        center, size ,angle = fitEllipse(shapePoints)
        
        cos_angle = np.cos(np.radians(180.-angle))
        sin_angle = np.sin(np.radians(180.-angle))
        
        xc = point[0] - center[0]
        yc = point[1] - center[1]
        
        xct = xc * cos_angle - yc * sin_angle
        yct = xc * sin_angle + yc * cos_angle 
        
        rad_cc = (xct**2/(size[0]/2.)**2) + (yct**2/(size[1]/2.)**2)
        return rad_cc<=1
        
    """
        Remove all polygons that the point falls inside.
    """
    """
    def removePolygon(self, point):
        for i in range(0,len(self.shapesListFrames)):
            if i>=len(self.shapesListFrames):
                break
                
            polygon = Polygon(self.shapesListFrames[i]);
            if polygon.contains(Point(point[0],point[1])):
                del self.shapesListFrames[i]
                i = i-1
    """
    
    def showAllShapes(self, img):
        DEBUG = False
        shapePointsCurrentXYRead = self.getShapePointsCurrentXYRead()
        borderPointsCurrentXYRead = self.getBorderPointsCurrentXYRead()
        #print('borderPointsCurrentXYRead: ',borderPointsCurrentXYRead)
        
        """
            Update current XY, and frame #
        """
        self.currentXYWell = self.frameCtrl.getCurrentXYWellNumber()
        self.currentFrame = self.frameCtrl.getCurrentFrameNumber()

        """
            Show shapes from prev frame
        """
        if self.showShapesFromPrevFrame is not None and self.showShapesFromPrevFrame!=self.currentFrame:
            for i in range(len(shapePointsCurrentXYRead[self.showShapesFromPrevFrame])):
                shapeType = self.shapeType(shapePointsCurrentXYRead[self.showShapesFromPrevFrame][i])
                self.showShape(img, shapePointsCurrentXYRead[self.showShapesFromPrevFrame][i], shapeType, self.shapesListFramesID[self.currentXYWell][self.showShapesFromPrevFrame][i], buildingShape=False, showAsCrosshairs=True)
        
        """
            Show all finished shapes from this frame
        """        
        for i in range(len(shapePointsCurrentXYRead[self.currentFrame])):
            shapeType = self.shapeType(shapePointsCurrentXYRead[self.currentFrame][i])
            if DEBUG:
                center = self.__getShapeCenter(shapePointsCurrentXYRead[self.currentFrame][i])
                print('   DEBUG: showing shape @ frame #'+np.str(self.currentFrame)+' shape index #'+np.str(i)+' @ pos=('+np.str(np.round(center[0],1))+','+np.str(np.round(center[1],1))+') ID #'+np.str(self.shapesListFramesID[self.currentXYWell][self.currentFrame][i]))
            self.showShape(img, shapePointsCurrentXYRead[self.currentFrame][i], shapeType, self.shapesListFramesID[self.currentXYWell][self.currentFrame][i], buildingShape=False)
            # Show border
            if len(borderPointsCurrentXYRead[self.currentFrame])>=i+1:
                shapeType = self.shapeType(borderPointsCurrentXYRead[self.currentFrame][i])
                self.showShape(img, borderPointsCurrentXYRead[self.currentFrame][i], shapeType, self.shapesListFramesID[self.currentXYWell][self.currentFrame][i], buildingShape=False, borderShape=True, showIndex=False)
            
        """
            Show the one we are working on right now
        """
        shapeType = self.shapeType(self.shapePoints)
        if not anyNonEmpty(self.shapesListFramesID[self.currentXYWell]):
            index = 0
        else:
            indexes = []
            for t in range(len(self.shapesListFramesID[self.currentXYWell])):
                for shapeID in range(len(self.shapesListFramesID[self.currentXYWell][t])):
                    index = self.shapesListFramesID[self.currentXYWell][t][shapeID]
                    if not_equal(index, self.missingShapeIDValue):
                        indexes.append(index)
            
            if len(indexes)==0:
                index = 0
            else:
                index = np.max(indexes)+1
        self.showShape(img, self.shapePoints, shapeType, index, buildingShape=True)
        # Show border
        if len(self.borderPoints)>=3:
            shapeType = self.shapeType(self.borderPoints)
            self.showShape(img, self.borderPoints, shapeType, index, buildingShape=True, borderShape=True, showIndex=False)
                
    """
        Draws the shape, whatever it may be, in img
         - index: the number corresponding to the shape
         - shapeType: what is the type of this shape
         - shapePoints: the points of the shape / that the shape is fit to
         - buildingShape: are we in the process of making the shape
         - showAsCrosshairs: don't draw the shape, draw a crosshair
    """
    def showShape(self, img, shapePoints, shapeType, index, buildingShape, showAsCrosshairs=False, borderShape=False, showIndex=True):
        if len(shapePoints)>=1 and showAsCrosshairs:
            center = self.__getShapeCenter(shapePoints)
            drawCross(img, center[0], center[1], self.shapeCrossRGB)
            return
        
        if shapeType=='polygon':
            if borderShape:
                self.showPolygon(img, shapePoints, index, buildingShape, borderShape, showIndex)
            else:
                self.showPolygon(img, shapePoints, index, buildingShape, borderShape, showIndex)
                self.showPoints(img, shapePoints, index)
        elif shapeType=='ellipse':
            center, size ,angle = fitEllipse(shapePoints)
            if borderShape:
                self.showEllipse(img, center, size ,angle, index, buildingShape, borderShape, showIndex)
            else:
                self.showEllipse(img, center, size ,angle, index, buildingShape, borderShape, showIndex)
                self.showPoints(img, shapePoints, index)
        elif shapeType=='circle':
            center, radius = fitCircle(shapePoints)
            if borderShape:
                self.showCircle(img, center, radius, index, buildingShape, borderShape, showIndex)
            else:
                self.showCircle(img, center, radius, index, buildingShape, borderShape, showIndex)
                self.showPoints(img, shapePoints, index)
        elif shapeType=='points':
            if len(shapePoints)>=1:
                self.showPoints(img, shapePoints, index)
                # Draw the number
                if not buildingShape and showIndex:
                    self.showIndex(img, index, shapePoints[0])
    
    """
        Draws points (as red squares) in the img
    """
    def showPoints(self, img, shapePoints, index):
        # just draw the points
        for pt in shapePoints:
            drawRect(img, pt[0], pt[1], L=2)
    
    """
        Draws a circle in the img
    """
    def showCircle(self, img, center, radius, index, buildingShape, borderPointsFlag=False, showIndex=True):
        """
            - You need to swap:
                x <-> y
        """
        oldcenter = tuple(np.array(center, dtype=int))
        center = tuple(np.array(center, dtype=int)[::-1])
        radius = np.int(radius)
        if borderPointsFlag:
            if buildingShape:
                color = np.copy(self.borderRGBBuilding)
            else:
                color = np.copy(self.borderRGBComplete)
        else:
            if buildingShape:
                color = np.copy(self.shapeRGB)
            else:
                # Red
                color = (255, 0, 0)
        color = color[::-1] #(255,255,255)
        cv2.circle(img, center, radius, color, 1)
        
        # Draw the number
        if not buildingShape and showIndex:
            self.showIndex(img, index, oldcenter)
        
    """
        Draws an ellipse in the img
    """
    def showEllipse(self, img, center, size ,angle, index, buildingShape, borderPointsFlag=False, showIndex=True):
        """
            - You need to swap:
                x <-> y
            - We are sending HALF the size, with (x,y) swapped
            - The angle is rotated by 90 degrees due to x,y swap
        """
        oldcenter = tuple(np.array(center, dtype=int))
        center = tuple(np.array(center, dtype=int)[::-1])
        size = tuple(np.array(size, dtype=int)[::-1]/2)
        angle -= 90.0
        if borderPointsFlag:
            if buildingShape:
                color = np.copy(self.borderRGBBuilding)
            else:
                color = np.copy(self.borderRGBComplete)
        else:
            if buildingShape:
                color = np.copy(self.shapeRGB)
            else:
                # Red
                color = (255, 0, 0)
        color = color[::-1] #(255,255,255)
        cv2.ellipse(img, center, size, angle, 0.0, 360.0, color=color, thickness=1)
        
        # Draw the number
        if not buildingShape and showIndex:
            self.showIndex(img, index, oldcenter)
        
    """
        Draws the lines that make up the polygon
    """
    def showPolygon(self, img ,shapePoints, index, buildingShape, borderPointsFlag=False, showIndex=True): 
        if len(shapePoints)==0:
            return
        
        """
            Sort the points to draw the polygon in the right order
        """
        #print('DEBUG: poly shapePoints: ',shapePoints)
        np.save(self.saveDir + 'workingPolygon.npy', np.array(shapePoints, dtype=object))
        
        polyFinder = PolygonShapeFinder(shapePoints)
        shapePoints = polyFinder.getSortedPolygon()
        
        # Draw the lines
        prevPt = None
        if borderPointsFlag:
            if buildingShape:
                color = np.copy(self.borderRGBBuilding)
            else:
                color = np.copy(self.borderRGBComplete)
        else:
            if buildingShape:
                color = np.copy(self.shapeRGB)
            else:
                # Red
                color = (255, 0, 0)
        for pt in shapePoints:
            if prevPt is not None:
                drawLine(img,prevPt,pt,color)
            prevPt = pt
            
        # Draw the number
        if not buildingShape and showIndex:
            self.showIndex(img, index, shapePoints[0])
        #cv2.putText(img,'#'+str(index),(shapePoints[0][1]+10,shapePoints[0][0]), self.font, 0.5,(100,255,0),1)
    
    """
        Draw the shape #
    """
    def showIndex(self, img, index, point):
        # Draw the circle number
        cv2.putText(img,'#'+str(index),(point[1]+10,point[0]), self.font, 0.5,(100,255,0),1)

    def __getShapeArray(self, fill, dtype):
        """
            We need to convert self.shapesListFrames to a numpy array in order to save it to file.
            The problem is than a numpy array must be square (in 3 dimensions), but we have a list
            of shapes per frame, where the number of shapes may change, and the number of points
            per shapes may change as well.
        """
        shapes = self.getShapePointsWrite()#self.__getShapesSortedByID()
        #shapes = self.__getShapesSortedByID()
        
        """
            Get numbr of XY wells
        """
        wellsNum = len(shapes)
        
        """
            Get number of frames
        """
        lens1 = [len(l) for l in shapes]
        maxFrames = np.max(lens1)
    
        """
            Find the maximum number of shapes in any frame
        """
        lens2 = [len(l2) for l1 in shapes for l2 in l1]
        maxShapes = np.max(lens2)
        
        """
            Find the maximum number of points per shape
        """
        lens3 = [len(l3) for l1 in shapes for l2 in l1 for l3 in l2]
        maxPointsPerShape = np.max(lens3)
        
        """
            data if filled with 'fill'
        """
        data = np.full((wellsNum,maxFrames,maxShapes,maxPointsPerShape,2),fill,dtype=dtype)
        
        """
            Fill in the data where we have points
        """
        for xy in range(wellsNum):
            for t in range(len(shapes[xy])):
                for shapeIndex in range(len(shapes[xy][t])):
                    for pointIndex in range(len(shapes[xy][t][shapeIndex])):
                        """
                            Make sure to divide by screen factor to get the absolute pixel coordinates
                            and not relative to this monitor
                        """
                        data[xy][t][shapeIndex][pointIndex,:] = np.array(np.array(shapes[xy][t][shapeIndex][pointIndex],dtype=np.float64)/self.screenFactor,dtype=np.float64)
            
        return data
    
    def __getShapeBorder(self, fill, dtype):
        shapeBorders = self.getBorderPointsWrite()
        shapes = self.getShapePointsWrite()
        #print('__getShapeBorder: shapeBorders[self.currentXYWell][self.currentFrame] = ',shapeBorders[self.currentXYWell][self.currentFrame])
        
        """
            Get numbr of XY wells
        """
        wellsNum = len(shapes)
        
        """
            Get number of frames
        """
        lens1 = [len(l) for l in shapes]
        maxFrames = np.max(lens1)
    
        """
            Find the maximum number of shapes in any frame
        """
        lens2 = [len(l2) for l1 in shapes for l2 in l1]
        maxShapes = np.max(lens2)
        
        """
            Find the maximum number of points per shape
            (this is for shape borders and not shapes as shape borders
            will have more points due to the method used to "expand" the
            shapes)
        """
        lens3 = [len(l3) for l1 in shapeBorders for l2 in l1 for l3 in l2]
        maxPointsPerShape = np.max(lens3)
        
        """
            data if filled with 'fill'
        """
        data = np.full((wellsNum,maxFrames,maxShapes,maxPointsPerShape,2),fill,dtype=dtype)
        
        """
            Fill in the data where we have points
        """
        for xy in range(wellsNum):
            for t in range(len(shapeBorders[xy])):
                for shapeIndex in range(len(shapeBorders[xy][t])):
                    #if not_equal(shapeBorders[xy][t][shapeIndex], self.missingShapeBorder):
                    for pointIndex in range(len(shapeBorders[xy][t][shapeIndex])):
                        
                        #shapeBorders[xy]
                        #shapeBorders[xy][t]
                        #shapeBorders[xy][t][shapeIndex]
                        #shapeBorders[xy][t][shapeIndex][pointIndex]
                        
                        """
                            Make sure to divide by screen factor to get the absolute pixel coordinates
                            and not relative to this monitor
                        """
                        #if len(shapeBorders)>xy and len(shapeBorders[xy])>t and len(shapeBorders[xy][t])>shapeIndex and len(shapeBorders[xy][t][shapeIndex])>pointIndex:
                        data[xy][t][shapeIndex][pointIndex,:] = np.array(np.array(shapeBorders[xy][t][shapeIndex][pointIndex],dtype=np.float64)/self.screenFactor,dtype=np.float64)
        #print('data[self.currentXYWell][self.currentFrame] =  ',data[self.currentXYWell][self.currentFrame])
        return data
    
    def __getShapeIDArray(self, fill, dtype):
        shapeID = self.shapesListFramesID
        
        """
            Get numbr of XY wells
        """
        wellsNum = len(shapeID)
        
        """
            Get number of frames
        """
        lens1 = [len(l) for l in shapeID]
        maxFrames = np.max(lens1)
        
        """
            Find the maximum number of shapes in any frame
        """
        lens2 = [len(l2) for l1 in shapeID for l2 in l1]
        maxShapes = np.max(lens2)
        
        """
            data if filled with 'fill'
        """
        data = np.full((wellsNum,maxFrames,maxShapes),fill,dtype=dtype)
        
        """
            Fill in the data where we have points
        """
        for xy in range(wellsNum):
            for t in range(len(shapeID[xy])):
                for shapeIndex in range(len(shapeID[xy][t])):
                    if not_equal(shapeID[xy][t][shapeIndex], self.missingShapeIDValue):
                        data[xy][t][shapeIndex] = shapeID[xy][t][shapeIndex]
        
        return data
        
    def __getShapeZArray(self, fill, dtype):
        shapeZ = self.shapesListFramesZ
        
        """
            Get numbr of XY wells
        """
        wellsNum = len(shapeZ)
        
        """
            Get number of frames
        """
        lens1 = [len(l) for l in shapeZ]
        maxFrames = np.max(lens1)
        
        """
            Find the maximum number of shapes in any frame
        """
        lens2 = [len(l2) for l1 in shapeZ for l2 in l1]
        maxShapes = np.max(lens2)
        
        """
            data if filled with 'fill'
        """
        data = np.full((wellsNum,maxFrames,maxShapes),fill,dtype=dtype)
        
        """
            Fill in the data where we have points
        """
        for xy in range(wellsNum):
            for t in range(len(shapeZ[xy])):
                for shapeIndex in range(len(shapeZ[xy][t])):
                    if not_equal(shapeZ[xy][t][shapeIndex], self.missingShapeZValue):
                        data[xy][t][shapeIndex] = shapeZ[xy][t][shapeIndex]
        
        return data
    
    def getShapePointsReadOriginalScale(self):
        shapePointsOriginalScale = []
        
        shapePointsOriginalScale = []
        for xy in range(len(self.shapesListFrames)):
            shapePointsOriginalScale.append([])
            for t in range(len(self.shapesListFrames[xy])):
                shapePointsOriginalScale[xy].append([])
                for shape in range(len(self.shapesListFrames[xy][t])):
                    shapePointsOriginalScale[xy][t].append([])
                    for point in range(len(self.shapesListFrames[xy][t][shape])):
                        shapePointsOriginalScale[xy][t][shape].append(np.array(np.array(self.shapesListFrames[xy][t][shape][point], dtype=np.float64)/self.screenFactor, dtype=int))

        return shapePointsOriginalScale
    
    def getBorderPointsReadOriginalScale(self):
        borderPointsOriginalScale = []
        
        for xy in range(len(self.bordersListFrames)):
            borderPointsOriginalScale.append([])
            for t in range(len(self.bordersListFrames[xy])):
                borderPointsOriginalScale[xy].append([])
                for shape in range(len(self.bordersListFrames[xy][t])):
                    borderPointsOriginalScale[xy][t].append([])
                    for point in range(len(self.bordersListFrames[xy][t][shape])):
                        borderPointsOriginalScale[xy][t][shape].append(np.array(np.array(self.bordersListFrames[xy][t][shape][point], dtype=np.float64)/self.screenFactor, dtype=int))
    
        return borderPointsOriginalScale
    
    def exportShapesToUNet(self, outputDir):   
        print('Exporting to UNet...')
        frameWidth = self.frameCtrl.getFrameWidth()
        frameHeight = self.frameCtrl.getFrameHeight()
        print('   frame width = '+np.str(frameWidth))
        print('   frame height = '+np.str(frameHeight))
        print('   output folder = '+outputDir)

        #imageArray = [[], []]
        #imageArray[0].append((2,))
        
        exporter = exportToUNet()
        exporter.export(self.frameCtrl,
                        self.getShapePointsReadOriginalScale(),
                        self.getBorderPointsReadOriginalScale(),
                        frameWidth,
                        frameHeight,
                        outputDir)
        print('   All done!')
    
    """
        This saves all the points for all the shapes, across all the frames
        to the outputfiilename (*.npy file).
    """
    def saveShapes(self, outputFilename):
        if self.__preEditCurrentXYPointsStored():
            self.__restorePreEditCurrentXYPoints()
        
        shapePointsWrite = self.getShapePointsWrite()
        
        """
            Are there any shapes to save?
        """
        flagAtLeastOneShape = False
        for xy in range(len(self.shapesListFrames)):
            for t in range(len(shapePointsWrite[xy])):
                if len(self.shapesListFrames[xy][t])>0:
                    flagAtLeastOneShape = True
        if not flagAtLeastOneShape:
            print('   saveShapes(): No shapes to save!')
            return
        
        """
            Make sure folder(s) exists
        """
        createFolder(ntpath.dirname(outputFilename))
        
        dataShapes = self.__getShapeArray(self.coordinateFillerValue, np.float64)
        dataShapeBorder = self.__getShapeBorder(self.coordinateFillerValue, np.float64)
        dataShapeID = self.__getShapeIDArray(self.coordinateFillerValue, np.int)
        dataShapeZ = self.__getShapeZArray(self.coordinateFillerValue, np.int)
        
        #print('dataShapeBorder: ',dataShapeBorder)
        
        now = datetime.datetime.now()
        if type(dataShapes) is not list:
            dataShapes = dataShapes.tolist()
        if type(dataShapeBorder) is not list:
            dataShapeBorder = dataShapeBorder.tolist()
        if type(dataShapeID) is not list:
            dataShapeID = dataShapeID.tolist()
        if type(dataShapeZ) is not list:
            dataShapeZ = dataShapeZ.tolist()
        data = {'shapes' : dataShapes
                , 'shape border' : dataShapeBorder
                , 'shape ID' : dataShapeID
                , 'shape Z' : dataShapeZ
                , 'frame skip' : self.frameSkip
                , 'organoidTracker version' : self.organoidTrackerVersion
                , 'saving date & time' : now}
        #data = np.array(data,dtype=object)
        
        """
            Save to file
        """
        if outputFilename.endswith('.npy'):
            outputFilename = outputFilename.replace('.npy','.json')
        if not outputFilename.endswith('.json'):
            outputFilename += '.json'
        
        print('   Saving all shape data to: '+outputFilename+'...')
        #np.save(outputFilename, data)
        with open(outputFilename, 'w') as outfile:
            json.dump(data, outfile, default=json_util.default)
        
        print('   Done!')
        
    """
        # of frames to skip between the frames you are seeing
    """
    def getFrameSkip(self):
        return self.frameSkip
    
    """
        # of frames to skip between the frames you are seeing
    """
    def setFrameSkip(self, frameSkip):
        self.frameSkip = frameSkip
        
    def getBackupTimedate(self):
        backupFilename = self.trackingDirectory + 'shapes.backup.json'
        if os.path.exists(backupFilename):
            with open(backupFilename, 'r') as f:
                data = json.load(f, object_hook=json_util.object_hook)
                
            if 'saving date & time' in data:
                return data['saving date & time']
        
        """
        backupFilename = self.trackingDirectory + 'shapes.backup.npy'
        
        if os.path.exists(backupFilename):
            data = np.load(backupFilename).item()
            
            if 'saving date & time' in data:
                return data['saving date & time']
        """
        
        return None
        
    def loadShapes(self, loadDir, inputFilename):
        DEBUG = False
        
        if DEBUG:
            inputFilename = 'D:/2018122_MIS_SOK015.nd2_tracking/shapes.npy'
            print('DEBUG: setting input filename to: ',inputFilename)
        
        inputFilenameJson = None
        if inputFilename.endswith('.json'):
            inputFilenameJson = copy.deepcopy(inputFilename)
        if inputFilename.endswith('.npy'):
            inputFilenameJson = inputFilename.replace('.npy', '.json')
        
        # Make sure the file exists:
        if not os.path.exists(inputFilename) and not os.path.exists(inputFilenameJson):
            print("   loadShapes() -- Error: input file doesn't exist!")
            print('   inputFilename: ',inputFilenameJson)
            return False
        
        if os.path.exists(inputFilenameJson):
            with open(inputFilenameJson, 'r') as f:
                data = json.load(f, object_hook=json_util.object_hook)
        else:
            # Load shapes
            data = np.load(inputFilename).item()
        dataShapes = data['shapes']
        dataShapeID = data['shape ID']
        #print('dataShapes.shape = ',dataShapes.shape)
        #print('dataShapeID.shape = ',dataShapeID.shape)
        dataShapeZ = data['shape Z']
        if 'shape border' in data:
            dataShapeBorder = data['shape border']
            #dataShapeBorder = None
        else:
            dataShapeBorder = None
            
        if type(dataShapes) is list:
            dataShapes = np.array(dataShapes)
        if type(dataShapeBorder) is list:
            dataShapeBorder = np.array(dataShapeBorder)
        if type(dataShapeID) is list:
            dataShapeID = np.array(dataShapeID)
        if type(dataShapeZ) is list:
            dataShapeZ = np.array(dataShapeZ)
        
        if 'saving date & time' in data:
            saveTime = data['saving date & time']
        else:
            saveTime = None
        
        """
            If the date/time of the backup file is more recent
            ask whether to load from backup instead
        """
        backupTime = self.getBackupTimedate()
        #print('backupTime: ',backupTime)
        #print('saveTime: ',saveTime)
        if (backupTime is not None and saveTime is not None) and (backupTime > saveTime):
            if boolQuestionMBox("The backup file is more recent.\rLoad from backup instead?"):
                self.loadBackup()
                
                """
                    We need to update the screen
                """
                self.updateScreenFlag = True
                
                return True
        
        """
            Get number of frames
            Add fake frames to start if we have too few
        """
        currentNumFrames = self.frameCtrl.getFrameCount()
        numFrames = dataShapes.shape[1]
        print('... Loading #'+np.str(numFrames)+' frames...')
        if numFrames<currentNumFrames:
            print('   Error we have more frames than are loaded! Aborting!')
            return
        elif numFrames==currentNumFrames:
            print('   Success! We have the same number of frames as are loaded!')
        else:
            numFakeFrames = numFrames-currentNumFrames
            print('   We have less frames than are loaded!')
            print('   We will add #'+np.str(numFakeFrames)+' fake frames to the beginning!')
            self.frameCtrl.addFakeFramesToBeginning(numFakeFrames)
            
        """
            If there is just one active XY channel pick that one (DEBUG)
        """
        if DEBUG:
            activeXY = -1
            numActiveXY = 0
            for xy in range(dataShapes.shape[0]):
                if any_not_equal(dataShapes[xy], self.coordinateFillerValue):
                    activeXY = xy
                    numActiveXY += 1
            if numActiveXY==1:
                print('   DEBUG: a single active xy found ('+np.str(activeXY)+')... setting to it...')
                self.frameCtrl.setXYWell(activeXY+1)
                
                """
                    Move either to the first or last frame,
                    depending where there are shapes.
                """
                DEBUG_SET_TO_MAX_AREA_FRAME = False
                
                if True:
                    self.frameCtrl.gotoFrame(35)
                
                elif not DEBUG_SET_TO_MAX_AREA_FRAME:
                    if any_not_equal(dataShapes[activeXY][-1],self.coordinateFillerValue):
                        print('   Setting frame to last...')
                        self.frameCtrl.gotoLastFrame()
                    else:
                        print('   Setting frame to first...')
                        self.frameCtrl.gotoFirstFrame()
                else:
                    print('   Setting frame to where the organoid area is maximized')
                    maxArea = 0
                    maxAreaFrame = -1
                    for t in range(dataShapes.shape[1]):
                        for i in range(dataShapes.shape[2]):
                            shapePoints = dataShapes[activeXY][t][i]
                            if not any_not_equal(shapePoints,self.coordinateFillerValue):
                                continue
                            shapeType = self.shapeType(shapePoints)
                            shapeArea = self.__getShapeArea(shapePoints,shapeType,1)
                            if shapeArea>maxArea:
                                maxArea = np.copy(shapeArea)
                                maxAreaFrame = np.copy(t)
                    print('   maxArea: ',maxArea)
                    print('   maxAreaFrame: ',maxAreaFrame)
                    self.frameCtrl.gotoFrame(maxAreaFrame)
        
        if 'frame skip' in data:
            self.frameSkip = data['frame skip']
        
        """
            Backwards compatibility -- do not do screen factor correction when loading if a certain
                                        file is present.
                                        
            LONGER:
                    The video is scaled according to monitor size, to fit entirely on the monitor.
                The points of the shapes thus are also scaled (multiplied) by this factor (it is the
                same for width and height, to maintain video aspect ratio).
                    In the previous versions of the software the points were saved after scaling. In
                this version, we divide by the factor before saving the points, then multiply
                by the (possibly different, if on a different monitor) factor when loading them
                again.
                    To maintain compatibility between the versions there is an option to load
                without multiplying by the screen factor (if the shapes were saved
                with the previous version of the software). When the shapes are saved
                this time, the points will be divided by the screen factor and so
                we delete this non-correction flag file ('screenFactor.npy').
        """
        screenFactorCorrectionFlag = True
        #screenFactorFilename = loadDir+'/'+'screenFactor.npy'
        if 'organoidTracker version' not in data or data['organoidTracker version']<0.050:#os.path.exists(screenFactorFilename):
            screenFactorCorrectionFlag = False
            print('   Ignoring screen factor for backwards compatibility...')
            
        if screenFactorCorrectionFlag:
            pointFactor = self.screenFactor
        else:
            pointFactor = 1
        
        self.shapesListFrames = []
        shapePointsWrite = self.getShapePointsWrite()
        self.bordersListFrames = []
        borderPointsWrite = self.getBorderPointsWrite()
        self.shapesListFramesID = []
        self.shapesListFramesZ = []
        
        for xy in range(dataShapes.shape[0]):
            shapePointsWrite.append([])
            self.shapesListFramesID.append([])
            self.shapesListFramesZ.append([])
            borderPointsWrite.append([])
            for t in range(dataShapes.shape[1]):
                shapePointsWrite[xy].append([])
                self.shapesListFramesID[xy].append([])
                self.shapesListFramesZ[xy].append([])
                borderPointsWrite[xy].append([])
                for shapeIndex in range(dataShapes.shape[2]):
                    """
                    borderPointsWrite = extendList(borderPointsWrite, xy, t, shapeIndex)
                    if dataShapeBorder is not None:
                        if len(dataShapeBorder)>xy and len(dataShapeBorder[xy])>t and len(dataShapeBorder[xy][t])>shapeIndex and dataShapeBorder[xy][t][shapeIndex]!=-1:
                            #borderPointsWrite[xy][t][shapeIndex] = dataShapeBorder[xy][t][shapeIndex]
                            borderPointsWrite[xy][t][shapeIndex][pointIndex] = np.array(np.array(dataShapes[xy][t][shapeIndex][pointIndex],dtype=np.float64)*self.screenFactor,dtype=np.float64)
                        else:
                            #borderPointsWrite[xy][t][shapeIndex] = []
                            pass
                    """
                    #if dataShapeID[xy][t][shapeIndex]!=-1:
                    if dataShapeID[xy][t][shapeIndex]!=-1:
                        self.shapesListFramesID = extendList(self.shapesListFramesID, xy, t, shapeIndex)
                        self.shapesListFramesID[xy][t][shapeIndex] = dataShapeID[xy][t][shapeIndex]
                    else:
                        """
                            Missing shape ID:
                                add one only if there is a shape added (below)
                        """
                        #self.shapesListFramesID[xy][t][shapeIndex] = copy.deepcopy(self.missingShapeIDValue)
                        pass
                    
                    #if dataShapeZ[xy][t][shapeIndex]!=-1:
                    if dataShapeZ[xy][t][shapeIndex]!=-1:
                        self.shapesListFramesZ = extendList(self.shapesListFramesZ, xy, t, shapeIndex)
                        self.shapesListFramesZ[xy][t][shapeIndex] = dataShapeZ[xy][t][shapeIndex]
                    else:
                        """
                            Missing shape Z value:
                                add one only if there is a shape added (below)
                        """
                        #self.shapesListFramesZ[xy][t][shapeIndex] = copy.deepcopy(self.missingShapeZValue)
                        pass
                    
                    flagMissingBorder = dataShapeBorder is None or all_equal(dataShapeBorder[xy][t][shapeIndex], self.coordinateFillerValue)
                    flagShapeAdded = False # We only add a border if there is a shape added
                    
                    """
                        The points are padded by missing/invalid point entries.
                    """
                    for pointIndex in range(dataShapes.shape[3]):
                        if np.all(dataShapes[xy][t][shapeIndex][pointIndex]!=self.coordinateFillerValue):
                            # Only include this shape if there is at least one valid point
                            shapePointsWrite = extendList(shapePointsWrite, xy, t, shapeIndex, pointIndex)
                            #borderPointsWrite = extendList(borderPointsWrite, xy, t, shapeIndex, pointIndex)
                            flagShapeAdded = True
                            """
                                Multiply the points by screen factor to get the right position relative to the screen
                            """
                            shapePointsWrite[xy][t][shapeIndex][pointIndex] = np.array(np.array(dataShapes[xy][t][shapeIndex][pointIndex],dtype=np.float64)*pointFactor,dtype=np.float64)
                            #if not flagMissingBorder:
                            #    borderPointsWrite[xy][t][shapeIndex][pointIndex] = np.array(np.array(dataShapeBorder[xy][t][shapeIndex][pointIndex],dtype=np.float64)*pointFactor,dtype=np.float64)
                        else:
                            break
                    
                    """
                        The points are padded by missing/invalid point entries.
                    """
                    if not flagMissingBorder:
                        for pointIndex in range(dataShapeBorder.shape[3]):
                            if np.all(dataShapeBorder[xy][t][shapeIndex][pointIndex]!=self.coordinateFillerValue):
                                borderPointsWrite = extendList(borderPointsWrite, xy, t, shapeIndex, pointIndex)
                                if not flagMissingBorder:
                                    borderPointsWrite[xy][t][shapeIndex][pointIndex] = np.array(np.array(dataShapeBorder[xy][t][shapeIndex][pointIndex],dtype=np.float64)*pointFactor,dtype=np.float64)
                            else:
                                break
                            
                    if flagShapeAdded:
                        """
                            Only if there is a shape added do we add an empty ID / Z
                            if they are missing
                        """
                        
                        if dataShapeID[xy][t][shapeIndex]==-1:
                            self.shapesListFramesID = extendList(self.shapesListFramesID, xy, t, shapeIndex)
                            self.shapesListFramesID[xy][t][shapeIndex] = copy.deepcopy(self.missingShapeIDValue)
                            
                        if dataShapeZ[xy][t][shapeIndex]==-1:
                            self.shapesListFramesZ = extendList(self.shapesListFramesZ, xy, t, shapeIndex)
                            self.shapesListFramesZ[xy][t][shapeIndex] = copy.deepcopy(self.missingShapeZValue)
                            
                    if flagMissingBorder and flagShapeAdded:
                        """
                            Missing shape border
                        """
                        borderPointsWrite = extendList(borderPointsWrite, xy, t, shapeIndex)
                        borderPointsWrite[xy][t][shapeIndex] = copy.deepcopy(self.missingShapeBorder)
                    """
                        If the border contains an invalid point, set as missing shape border
                    """
                    if len(borderPointsWrite[xy][t])==shapeIndex+1:
                        if not_equal(borderPointsWrite[xy][t][shapeIndex], self.missingShapeBorder) and any_equal(borderPointsWrite[xy][t][shapeIndex], self.coordinateFillerValue):
                            borderPointsWrite[xy][t][shapeIndex] = copy.deepcopy(self.missingShapeBorder)
        
        #print('self.shapesListFrames: ',self.shapesListFrames)
        
        """
            Test loaded data for validity:
                FALSE: 1. The number of shapes must be the same across all frames
                1. You cannot have a shape with 0 points in all frames.
                2. Shapes may not have only 1 or 2 points.
                3. Each point must be two (x,y) coordinates.
        """
        
        """
            FALSE: 1. The number of shapes must be the same across all frames
        """
        """
        for xy in range(len(shapePointsWrite)):
            numShapes = len(shapePointsWrite[xy][0])
            for t in range(len(shapePointsWrite[xy])):
                if len(shapePointsWrite[xy][t])!=numShapes:
                    print('Number of shapes not equal on all frames!')
                    sys.exit()
        """
        
        """
            1. You cannot have a shape with 0 points in all frames.
        """
        dictShapePointsCount = dict()
        for xy in range(len(shapePointsWrite)):
            for t in range(len(shapePointsWrite[xy])):
                for shapeIndex in range(len(shapePointsWrite[xy][t])):
                    shapeID = self.shapesListFramesID[xy][t][shapeIndex]
                    if not_equal(shapeID, self.missingShapeIDValue):
                        for point in shapePointsWrite[xy][t][shapeIndex]:
                            if not any_equal(point, self.coordinateFillerValue):
                                if shapeID not in dictShapePointsCount:
                                    dictShapePointsCount[shapeID] = 0
                                dictShapePointsCount[shapeID] += 1
        
        removeShapeIDs = [shapeID for shapeID in dictShapePointsCount.keys() if dictShapePointsCount[shapeID]==0]
        
        for xy in range(len(shapePointsWrite)):
            for t in range(len(shapePointsWrite[xy])):
                while shapeIndex<len(shapePointsWrite[xy][t]):
                    shapeID = self.shapesListFramesID[xy][t][shapeIndex]
                    if shapeID in removeShapeIDs:
                        del shapePointsWrite[xy][t][shapeIndex]
                        del borderPointsWrite[xy][t][shapeIndex]
                        del self.shapesListFramesID[xy][t][shapeIndex]
                        del self.shapesListFramesZ[xy][t][shapeIndex]
                        shapeIndex -= 1
                    
                    shapeIndex += 1
        
        countInvalidPointsNum = 0
        countInvalidCoordinatesNum = 0
        for xy in range(len(shapePointsWrite)):
            for t in range(len(shapePointsWrite[xy])):
                #for shapeIndex in range(len(shapePointsWrite[xy][t])):
                while shapeIndex<len(shapePointsWrite[xy][t]):
                    if shapeIndex>len(shapePointsWrite[xy][t])-1:
                        break
                    
                    """
                        Shapes may not have only 1 or 2 points.
                    """
                    if len(shapePointsWrite[xy][t][shapeIndex])>0 and len(shapePointsWrite[xy][t][shapeIndex])<3:
                        #print('There is a shape with less than 3 points!')
                        countInvalidPointsNum += 1
                        
                        """
                            Remove offending shape from all frames!
                        """
                        del shapePointsWrite[xy][t][shapeIndex]
                        del borderPointsWrite[xy][t][shapeIndex]
                        del self.shapesListFramesID[xy][t][shapeIndex]
                        del self.shapesListFramesZ[xy][t][shapeIndex]
                        shapeIndex -= 1
                    else:
                        """
                            4. Each point must be two (x,y) coordinates.
                        """
                        for pointIndex in range(len(shapePointsWrite[xy][t][shapeIndex])):
                            if len(shapePointsWrite[xy][t][shapeIndex][pointIndex])!=2:
                                print('There is a point with !=2 coordinates!')
                                countInvalidCoordinatesNum += 1
                    shapeIndex += 1
        if countInvalidPointsNum>0:
            print('   We found and removed #'+np.str(countInvalidPointsNum)+' shapes with less than 3 points')
        if countInvalidCoordinatesNum>0:
            print('   We found #'+np.str(countInvalidCoordinatesNum)+' invalid coordinates (not 2D)')
        
        if not screenFactorCorrectionFlag:
            print('   Saving shapes with screen factor correction...')
            self.saveShapes(inputFilename)
            
            """
                After we saved the corrected data, we can remove the flagging file.
            """
            #os.remove(screenFactorFilename)
            
        """
            We need to update the screen
        """
        self.updateScreenFlag = True
        #print('shapePointsWrite: ',shapePointsWrite)
        #print('borderPointsWrite: ',borderPointsWrite)
        #print('self.shapesListFramesID: ',self.shapesListFramesID)
        #print('self.shapesListFramesZ: ',self.shapesListFramesZ)
        
        return True
        
    """
        Saves the shape areas to an *.npy file (outputFilename) and an excel
        file (outputExcelFilename).
    """
    def saveShapeAreas(self, outputFilename, outputExcelFilename):
        if self.__preEditCurrentXYPointsStored():
            self.__restorePreEditCurrentXYPoints()
        
        shapePointsWrite = self.getShapePointsWrite()
        
        """
            Are there any shapes to save?
        """
        flagAtLeastOneShape = False
        for xy in range(len(shapePointsWrite)):
            for t in range(len(shapePointsWrite[xy])):
                if len(shapePointsWrite[xy][t])>0:
                    flagAtLeastOneShape = True
        if not flagAtLeastOneShape:
            print('   saveShapeAreas(): No shapes to save!')
            return
        
        """
            Make sure folder(s) exists
        """
        createFolder(ntpath.dirname(outputFilename))
        createFolder(ntpath.dirname(outputExcelFilename))
        
        areas = self.__getShapeAreas(sortedByID=True)
        #print('areas: ',areas)
        
        """
            Save to file
        """
        if self.umpixel is not None:
            outputFilename += '[unit=um^2]'
            outputExcelFilename += '[unit=um^2]'
        else:
            outputFilename += '[unit=pixel^2]'
            outputExcelFilename += '[unit=pixel^2]'    
        print('   Saving all shape areas to: '+outputFilename+'.npy...')
        np.save(outputFilename, areas)
        print('   Done!')
        
        """
            Output to excel
        """
        print('   Saving all shape areas to: '+outputExcelFilename+'_XY_#.xlsx...')
        """
            -1 here is the value to be ignored in the matrix...
        """
        self.__shapeAreasToExcel(outputExcelFilename, areas, self.areaFillerValue)
        print('   Done!')
        
    def __getShapeAreas(self, sortedByID=False):
        if sortedByID:
            shapes = self.__getShapesSortedByID(dtype=np.float64)
        else:
            shapes = self.getShapePointsWrite()
        #print('Current well #'+np.str(self.currentXYWell))
        #print('shapes: ',shapes)
        #print('shapes[0] len = ',len(shapes[0]))
        #print('shapes[0][80] = ',shapes[0][80])
        
        """
            Get numbr of XY wells
        """
        wellsNum = len(shapes)
        
        """
            Get number of frames
        """
        lens1 = [len(l) for l in shapes]
        maxFrames = np.max(lens1)
        #print('max frames: ',maxFrames)
    
        """
            Find the maximum number of shapes in any frame
        """
        lens2 = [len(l2) for l1 in shapes for l2 in l1]
        maxShapes = np.max(lens2)
        
        """
            Find areas
        """
        #shapePointsCurrentXYRead = self.getShapePointsCurrentXYRead()
        areas = np.full((wellsNum,maxFrames,maxShapes), self.areaFillerValue, dtype=np.int64)
        for xy in range(wellsNum):
            for t in range(len(shapes[xy])):
                for shapeIndex in range(len(shapes[xy][t])):
                    shapePoints = shapes[xy][t][shapeIndex]
                    if len(shapePoints)>0:
                        area = self.__getShapeArea(shapePoints,self.shapeType(shapePoints), self.screenFactor)
                        areas[xy][t][shapeIndex] = area
                        if areas[xy][t][shapeIndex]==0:
                            areas[xy][t][shapeIndex] = self.areaFillerValue
        return areas
        
    """
    def loadShapeAreas(self, inputFilename):
        # Make sure the file exists:
        if not os.path.exists(inputFilename):
            print("loadShapeAreas() -- Error: input file doesn't exist!")
            return
        
        # Load shapes
        areas = np.load(inputFilename)
        self.shapesListFrames = []
        for t in range(areas.shape[0]):
            for shapeIndex in range(areas.shape[1]):
                if areas[t][shapeIndex][pointIndex]!=-1:
                    self.shapesListFrames = extendList(self.shapesListFrames, t, shapeIndex)
                    self.shapesListFrames[t][shapeIndex] = areas[t][shapeIndex]
    """
    
    """
        Return the area of the current / last polygon. This area depends on the factor
        of by how much the pixels were inflated (hight and width was multiplied by).
        
        The area returned is in um**2 units.
    """
    def getPolyArea(self, factor):
        shapePointsCurrentXYRead = self.getShapePointsCurrentXYRead()
        return self.__getPolygonArea(shapePointsCurrentXYRead[self.currentFrame][-1])/np.power(factor,2)*(np.power(self.umpixel,2) if self.umpixel is not None else 1)
    
    """
        This assumes the order of areas per frame maintains the organoid id order.
        (first area on first frame is of he same organoid that the 1st area of the
        second frame belongs to and so on)
    """
    def __shapeAreasToExcel(self, outputExcelFilename, areas, invalidValue):
        """
            Don't write invalid data
        """
        areas = np.array(areas, dtype=object)
        areas[areas==invalidValue] = ''

        """
            Create data to write
        """
        for xy in range(areas.shape[0]):
            flagEmpty = True
            for t in range(areas.shape[1]):
                if np.any(areas[xy][t]!=''):
                    flagEmpty = False
                    break
            
            if flagEmpty:
                continue
            
            dataDict = dict()
            t = 0
            #print('self.frameCtrl.getFrameSkip(): ',self.frameCtrl.getFrameSkip())
            for i in range(0,areas.shape[1],self.frameCtrl.getFrameSkip()):
                dataDict['t='+np.str(t)] = areas[xy][i]
                t += 1
            df = pd.DataFrame(dataDict)
            df = df.reindex(natsorted(df.columns), axis=1)
            
            numTimes = t
            numOrganoids = np.max([np.count_nonzero(areas[xy][t]!='') for t in range(len(areas[xy]))])
            
            """
                Write data
            """
            outputFilename = outputExcelFilename+'_XY_'+np.str(int(xy)+1)+'.xlsx'
            print('   Saving excel XY='+np.str(int(xy)+1))
            dataSheetName = 'XY '+np.str(int(xy)+1)
            
            writer = pd.ExcelWriter(outputFilename, engine='xlsxwriter')
            df.to_excel(writer,dataSheetName)
            #writer.save()
            
            """
            import xlsxwriter
            workbook  = xlsxwriter.Workbook(outputFilename)
            dataSheetName = 'XY '+np.str(int(xy)+1)
            worksheet = workbook.add_worksheet(dataSheetName)
            """
            
            """
                Create plots sheet
            """
            #print('numOrganoids: '+np.str(numOrganoids))
            #print('numTimes: '+np.str(numTimes))
            if numOrganoids<10:
                #plotSheetName = 'XY '+np.str(int(xy)+1)+' plots'
                workbook = writer.book
                #worksheet = workbook.add_worksheet(plotSheetName)
                
                worksheet = writer.sheets[dataSheetName]
                chart = workbook.add_chart({'type': 'scatter'})
                
                # Configure the series of the chart from the dataframe data.
                for row in range(1,numOrganoids+1):
                    chart.add_series({
                        'name':       [dataSheetName, row, 0],
                        'categories': [dataSheetName, 1, 0, numTimes, 0],
                        'values':     [dataSheetName, row, 1, row, numTimes],
                        'marker':     {'type': 'circle', 'size': 4},
                    })
                
                # Configure the chart axes.
                chart.set_x_axis({'name': 't'})
                chart.set_y_axis({'name': 'organoid size', 'major_gridlines': {'visible': False}})
            
                # Insert the chart into the worksheet.
                worksheet.insert_chart('D13', chart)
            
            writer.save()
            
        
    """
        This assumes the order of areas per frame maintains the organoid id order.
        (first area on first frame is of he same organoid that the 1st area of the
        second frame belongs to and so on)
    """
    def __shapeAreasXYToExcel(self, outputExcelFilename, areas, x, y, invalidValue):
        return
    
        """
            Don't write invalid data
        """
        areas = np.array(areas, dtype=object)
        areas[areas==invalidValue] = ''
        x = np.array(x, dtype=object)
        x[x==invalidValue] = ''
        y = np.array(y, dtype=object)
        y[y==invalidValue] = ''
        
        
        #dataDict['Frame']
        #dataDict['Area'] = #areas
        #dataDict['x'] = #x
        #dataDict['y'] = #y

        """
            Create data to write
        """
        dataDict = dict()
        for t in range(areas.shape[0]):
            dataDict['t='+np.str(t)] = areas[t]
        df = pd.DataFrame(dataDict)
        #df = df.reindex(natsorted(df.columns), axis=1)
        
        """
            Write data
        """
        writer = pd.ExcelWriter(outputExcelFilename+'.xlsx')
        df.to_excel(writer,'Sheet1')
        writer.save()
    
    """
        factor - the factor that the original width / height of the video was multiplied by
        to make it fit the window size wanted.
    """
    def __getShapeArea(self, shapePoints, shapeType, factor):
        conversionFactor = np.power(self.umpixel,2) if self.umpixel is not None else 1
        if shapeType=='circle':
            center, radius = fitCircle(shapePoints)
            return self.__getCircleArea(center, radius)/np.power(factor,2)*conversionFactor
        elif shapeType=='ellipse':
            center, size ,angle = fitEllipse(shapePoints)
            return self.__getEllipseArea(center, size ,angle)/np.power(factor,2)*conversionFactor
        elif shapeType=='polygon':
            return self.__getPolygonArea(shapePoints)/np.power(factor,2)*conversionFactor
        else:
            return 0
    
    def __getCircleArea(self, center, radius):
        return np.pi*np.power(radius,2)
    
    def __getEllipseArea(self, center, size ,angle):
        return np.pi*(size[0]/2)*(size[1]/2)
    
    def __getPolygonArea(self, points):
        x = np.array([pt[0] for pt in points],dtype=np.float64)
        y = np.array([pt[1] for pt in points],dtype=np.float64)
        return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

    def measureAveragePolyIntensity(self, grayImg, img, frame, shapePoints, index):
        global polyMaskList,polyMaskPointsList;#shapePoints,polyMask,polyMaskPoints;
        
        if len(shapePoints)<2:
            return;
        
        flagMask = False;
        if len(self.polyMaskPointsList)>index and len(self.polyMaskList)>index:
            if np.array_equal(np.array(shapePoints),np.array(self.polyMaskPointsList[index])):
                mask = self.polyMaskList[index];
                flagMask = True;
        if flagMask==False:
            mask = np.array(grayImg,dtype=bool);
            mask[:] = False;
            
            xpoints = [pt[0] for pt in shapePoints];
            ypoints = [pt[1] for pt in shapePoints];
            xmin = np.min(xpoints);
            xmax = np.max(xpoints);
            ymin = np.min(ypoints);
            ymax = np.max(ypoints);
            
            polygon = Polygon(shapePoints);
            for x in range(xmin,xmax+1):
                for y in range(ymin,ymax+1):
                    if polygon.contains(Point(x, y)):
                        mask[x,y] = True;
            
            self.polyMaskList = extendList(self.polyMaskList,index);
            self.polyMaskList[index] = mask;
            self.polyMaskPointsList = extendList(self.polyMaskPointsList,index);
            self.polyMaskPointsList[index] = np.copy(shapePoints);
        avgIntensity = np.mean(grayImg[mask]);
        
        # This test works:
        #img[mask] = (0,0,255);
        
        self.addPolyIntensity(index,frame,avgIntensity);
        #print('avgIntensity: ',avgIntensity);
        #return avgIntensity;
        
    def addPolyIntensity(index,frame,avgIntensity):
        global polyIntensities
        polyIntensities = extendList(polyIntensities,index)
        polyIntensities[index] = extendList(polyIntensities[index],frame)
        polyIntensities[index][frame] = avgIntensity
    
    def savePolyIntensities(self, filename):        
        if filename is not None:    
            csvOutputFile = filename + "polyIntensities.csv"
        else:
            csvOutputFile = "polyIntensities.csv"
            
        # In case we didn't start at the first frame
        for i in range(0,len(self.polyIntensities)):
            for frame in range(0,len(self.polyIntensities[i])):
                if self.polyIntensities[i][frame]==[]:
                    self.polyIntensities[i][frame] = -1
        
        for i in range(0,len(self.polyIntensities)):
            #
            # Output graph
            ##########################################
            fig = plt.figure(100)
            plt.plot(range(0,len(self.polyIntensities[i])),self.polyIntensities[i],'b')
            plt.xlabel('time [frame]')
            plt.ylabel('Poly Average Intenisty')
            plt.title('Poly Average Intensity as a Function of Time')
            fig.savefig(filename+"polyIntenistyPlot["+str(i)+"].jpeg")
            fig.clf()
            plt.close(fig)
            
        #
        # Output to *.CSV
        ##########################################
        if len(self.polyIntensities)>0:
            print('Writing to CSV file: ',csvOutputFile);
            with open(csvOutputFile, 'w') as csvfile:
                writer = csv.writer(csvfile, delimiter=',',\
                    quotechar='|', quoting=csv.QUOTE_MINIMAL,lineterminator='\n')
                
                # Write header row
                row1 = ['Frame #'];
                for i in range(0,len(self.polyIntensities)):
                    row1.append('poly '+str(i))
                writer.writerow(row1)
                    
                # Write data rows
                rows = [];
                for frame in range(0,len(self.polyIntensities[0])):
                    row = []
                    row.append(str(frame));
                    for i in range(0,len(self.polyIntensities)):
                        if polyIntensities[i][frame]==-1:
                            row.append("")
                        else:
                            row.append(str(self.polyIntensities[i][frame]))
                    rows.append(row)
                                    
                for i in range(0,len(rows)):
                    writer.writerow(rows[i])
        
    def clearPolyIntensities(self):
        self.polyIntensities = []

    def measureAveragePolyIntensityForAllPolys(self, grayImg, img, frame):
        shapePointsCurrentXYRead = self.getShapePointsCurrentXYRead()
        
        for i in range(0,len(shapePointsCurrentXYRead[self.currentFrame])):
            #measureAveragePolyIntensity(grayImg,img,frame,shapesList[i],i);
            selectedPixels = []
            selectedPixelsCoord = []
            linePoints = []
            for j in range(0,len(shapePointsCurrentXYRead[self.currentFrame][i])-1):
                selectedPixelsNew,selectedPixelsCoordNew = lineMgr.measureIntensityForLine(grayImg,img,frame,shapePointsCurrentXYRead[self.currentFrame][i][j],shapePointsCurrentXYRead[self.currentFrame][i][j+1],j)
                #print('selectedPixelsCoordNew: ',selectedPixelsCoordNew)
                if len(selectedPixels)==0:
                    selectedPixels = np.array(selectedPixelsNew);
                    selectedPixelsCoord = np.array(selectedPixelsCoordNew)
                    #linePoints = np.array([shapesList[i][j]])
                else:
                    selectedPixels = np.concatenate((selectedPixels,selectedPixelsNew))
                    selectedPixelsCoord = np.concatenate((selectedPixelsCoord,selectedPixelsCoordNew))
                    #linePoints = np.concatenate(linePoints,np.array([shapesList[i][j]]))
            linePoints = np.array(shapePointsCurrentXYRead[i])
            
            gDataDir = None
            if gDataDir is None:
                #folderNum = 0
                
                dataDir = 'selectedPixels/'+str(self.getCurrentFrame())
                """
                if os.path.exists(dataDir):
                    print('Checking for folder -- '+dataDir+': folder exists')
                    return
                    #folderNum = folderNum + 1
                    #dataDir = 'selectedPixels/'+str(folderNum)
                """
                
                if not os.path.exists(dataDir):
                    try:
                        print('Trying to create folder: '+dataDir)
                        os.makedirs(dataDir)
                    except:
                        print('Failed to create folder!')
                    print('Folder created!')
                gDataDir = dataDir
            
            # Save plot
            fig = plt.figure(100)
            plt.plot(range(0,len(selectedPixels)),selectedPixels)
            fig.savefig(gDataDir+'/selectedPixels['+str(frame)+'].png')
            fig.clf()
            plt.close(fig)
            
            # Save data
            np.save(gDataDir+'/selectedPixels['+str(frame)+']',selectedPixels)
            
            # Save line pts
            if os.path.exists(gDataDir+'/selectedPixels[points]')==False:
                np.save(gDataDir+'/selectedPixels[points]',linePoints)
            
            # Save coordinates for line
            if os.path.exists(gDataDir+'/selectedPixels[coord]')==False:
                np.save(gDataDir+'/selectedPixels[coord]',selectedPixelsCoord)
    
            if False:     
                #
                # Test coord.
                x,y = [],[]
                for c in selectedPixelsCoord:
                    x.append(c[1])
                    y.append(-c[0])
                fig = plt.figure(1010)
                plt.plot(x[:np.int(len(x)/2)],y[:np.int(len(x)/2)],'ro')
                plt.plot(x[np.int(len(x)/2):],y[np.int(len(x)/2):],'ko')
                fig.savefig(gDataDir+'/pixelsCoord.png')
                fig.clf()
                plt.close(fig)
                
if __name__=='__main__':
#      pointsManager = PointsManager(None)
    pass