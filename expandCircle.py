# -*- coding: utf-8 -*-
"""
Created on Mon Jul 02 17:07:08 2018

@author: Edward
"""

import numpy as np
from shapely.geometry import LineString, Point
import cv2
import copy

def fitCircle(points):
    center, radius = cv2.minEnclosingCircle(np.array(points))
    return center, radius

"""
    Expands the circle fit for circlePoints, untill the expanded
    circle touches the point.
    Returns the expanded circle
    
    flagExpand - does it allow only to expand the shape or only to collapse it? 
"""
def expandCircleUntillPoint(circlePoints, point, flagExpand=False):
    center, radius = fitCircle(circlePoints)
    newRadius = Point(center).distance(Point(point))
    center = np.array(center, dtype=np.float64)
    
    """
        The point is inside the original circle
    """
    if flagExpand:
        if newRadius<=radius:
            #return center, radius
            return circlePoints
    else:
        if newRadius>=radius:
            return circlePoints
    
    """
    #return center, newRadius
    return np.array(np.array(circlePoints-center,dtype=np.float64)/radius*newRadius + center, dtype=np.int32)
    """
    
    """
        Generate point for the new circle
    """
    newCirclePoints = []
    for _ in range(100):
        theta = np.random.random()*4*np.pi-2*np.pi
        x = center[0] + newRadius*np.cos(theta)
        y = center[1] + newRadius*np.sin(theta)
        newCirclePoints.append((x,y))
    return np.array(newCirclePoints, dtype=np.int64)