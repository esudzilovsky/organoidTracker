# -*- coding: utf-8 -*-
"""
Created on Fri Jun 29 13:53:04 2018

@author: Edward
"""

from __future__ import print_function

import numpy as np
import cv2
from cv2 import WINDOW_NORMAL
import itertools as IT
import copy
from shapely.geometry import LineString, Point
from expandPolygon import expandPolyUntillPoint
from expandCircle import expandCircleUntillPoint, fitCircle
from expandEllipse import expandEllipseUntillPoint, fitEllipse
from exportToUNet import exportToUNet

intersectionPt = None
polyCenterPt = None
pointPt = None
intersectionCenterLine = None
intersectionPointLine = None

scaledPolygonPts = None
scaledEllipsePts = None
scaledCirclePts = None
originalPolygonPoints = None
originalEllipsePoints = None
originalCirclePoints = None
class MouseControl:
    def __init__(self):        
        self.flagEditingShape = False
        self.trackx = None
        self.tracky = None
        self.lButtonDown = False
        
        self.updateScreenFlag = False
        self.flagSettingShapeBorder = False
    
    """
        Returns True if the screen needs to be updated
    """
    def updateScreen(self):
        return self.updateScreenFlag
    
    def setflagEditingShape(self, flag):
        self.flagEditingShape = flag
        
    def settingShapeBorder(self, flag):
        self.flagSettingShapeBorder = flag
        
    """
        Call this function to indicate you just updated the screen
    """
    def screenUpdated(self):
        self.updateScreenFlag = False
    
    def callback(self, event, x, y, flags, param):
        global originalPolygonPoints, originalCirclePoints, originalEllipsePoints
        global scaledPolygonPts, scaledCirclePts, scaledEllipsePts

        if event == cv2.EVENT_LBUTTONUP:
            pass
        
        elif event == cv2.EVENT_LBUTTONDOWN:#EVENT_MOUSEMOVE:
            #print('EVENT_LBUTTONDOWN')
            
            # We send the points as (x,y) directly when drawing,
            # so don't reverse the order
            point = (x,y)
            if originalPolygonPoints is not None:
                scaledPolygonPts = expandPolyUntillPoint(originalPolygonPoints, point)
            if originalCirclePoints is not None:
                scaledCirclePts = expandCircleUntillPoint(originalCirclePoints, point)
                #scaledCirclePts = fitCircle(scaledCirclePts)
            if originalEllipsePoints is not None:
                scaledEllipsePts = expandEllipseUntillPoint(originalEllipsePoints, point)
        
        if event == cv2.EVENT_RBUTTONDOWN:
            pass
    
        elif event == cv2.EVENT_LBUTTONUP:
            pass

pts = np.array([(180, 200), (260, 200), (260, 150), (180, 150), (100,150), (100,150), (100,150), (100,150), (100,150)], dtype=np.int32)
ellipsePts = np.array([(0,0), (100,0), (0, 100), (25, 50), (50, 25)], dtype=np.int32)
ellipseCenter = np.array([200,200], dtype=np.int32)
#scaledPolygonPts = expandPoly(pts, 2)
originalPolygonPoints = copy.deepcopy(pts)
#originalCirclePoints = copy.deepcopy(np.array([(180, 200), (260, 200), (260, 150)], dtype=np.int32))
#originalEllipsePoints = copy.deepcopy(ellipsePts+ellipseCenter)
#originalPolygonPoints = np.array([(100,200),(100,100)], dtype=np.int64)

"""
--------------------------------------------------------------------------------
"""

mouseCtrl = MouseControl()
cv2.namedWindow('image',WINDOW_NORMAL)
cv2.setMouseCallback('image', mouseCtrl.callback)
cv2.resizeWindow('image', 600,600)
img = np.zeros((600,600,3), dtype=np.uint8)

def showEllipse(img, center, size ,angle, color=(255, 0, 0)):
    """
        - You need to swap:
            x <-> y
        - We are sending HALF the size, with (x,y) swapped
        - The angle is rotated by 90 degrees due to x,y swap
    """
    #oldcenter = tuple(np.array(center, dtype=int))
    center = tuple(np.array(center, dtype=int)[::-1])
    size = tuple(np.array(size, dtype=int)[::-1]/2)
    angle -= 90.0
    color = color[::-1] #(255,255,255)
    cv2.ellipse(img, center, size, angle, 0.0, 360.0, color=color, thickness=1)

def showCircle(img, center, radius, color=(255, 0, 0)):
    center = tuple(np.array(center, dtype=int))
    radius = np.int(radius)
    color = color[::-1]
    cv2.circle(img, center, radius, color, 1)
    
def drawLine(pic,pt1,pt2,rgb=(255,255,255)):
    rgb = rgb[::-1]
    cv2.line(pic, (pt1[1],pt1[0]), (pt2[1],pt2[0]), rgb)
    
def showLine(img, line, color=(255, 0, 0)):
    pt0 = tuple(np.array(line[0], dtype=int))
    pt1 = tuple(np.array(line[1], dtype=int))
    drawLine(img,pt0,pt1,color)
    
while(1):
    img = np.zeros((600,600,3), dtype=np.uint8)       
    
    if originalPolygonPoints is not None:
        #print('printing original polygon')
        copyPoints = copy.deepcopy(originalPolygonPoints).reshape((-1,1,2))
        cv2.polylines(img,[copyPoints],True,(0,255,255))
        
        exporter = exportToUNet()
        mask = exporter.export(img, [[[originalPolygonPoints]]], None, len(img[0]), len(img))
    
    if scaledPolygonPts is not None:
        scaledPolygonPts = scaledPolygonPts.reshape((-1,1,2))
        cv2.polylines(img,[scaledPolygonPts],True,(0,255,255))
    
    if originalEllipsePoints is not None:
        center, size, angle = fitEllipse(originalEllipsePoints)
        #print('center, size, angle =',center, size, angle)
        showEllipse(img, center, size, angle, (255,255,0))
        
        exporter = exportToUNet()
        mask = exporter.export(img, [[[originalEllipsePoints]]], None, len(img[0]), len(img))
        
    if scaledEllipsePts is not None:
        center, size, angle = fitEllipse(scaledEllipsePts)
        #showEllipse(img, scaledEllipsePts[0], scaledEllipsePts[1], scaledEllipsePts[2], (255,255,0))
        showEllipse(img, center, size, angle, (255,255,0))
    
    if originalCirclePoints is not None:
        center, radius = fitCircle(originalCirclePoints)
        showCircle(img, center, radius,(255,255,0))
        
        #print('img.shape = '+np.str(img.shape))
        exporter = exportToUNet()
        mask = exporter.export(img, [[[originalCirclePoints]]], None, len(img[0]), len(img))
        
        #img[mask==exportToUNet.categoryOrganoid] = np.array((255,255,0))
        
    if scaledCirclePts is not None:
        showCircle(img, scaledCirclePts[0], scaledCirclePts[1],(255,255,0))
    
    # Draw intersection point
    if intersectionPt is not None:
        intersectionPt = np.array(intersectionPt, dtype=int)
        showCircle(img, intersectionPt, 5)
        #cv2.circle(img, intersectionPt, int(5), (0,0,255), 1)
        
    # Draw intersection lines
    if pointPt is not None:
        pointPt = np.array(pointPt, dtype=int)
        showCircle(img, pointPt, 5, (0,255,0))
    if polyCenterPt is not None:
        polyCenterPt = np.array(polyCenterPt, dtype=int)
        showCircle(img, polyCenterPt, 5, (0,0,255))
    if intersectionCenterLine is not None:
        intersectionCenterLine = np.array(intersectionCenterLine, dtype=int)
        showLine(img, intersectionCenterLine, (0,255,0))
    if intersectionPointLine is not None:
        intersectionPointLine = np.array(intersectionPointLine, dtype=int)
        showLine(img, intersectionPointLine, (0,0,255))
    
    cv2.imshow('image',img)   
    
    k = cv2.waitKey(33)
    if k==27:    # Esc key to stop
        break
    elif k==-1:  # normally -1 returned,so don't print it
        continue
    elif (k&0xFF == ord('q')) or (k&0xFF == ord('Q')):
        break
    elif k==6:
        print('CTRL+f')
    else:
        print(k) # else print its value
cv2.destroyAllWindows()

# solution (a list of paths): [[[240, 200], [190, 200], [190, 150], [240, 150]], [[200, 190], [230, 190], [215, 160]]]