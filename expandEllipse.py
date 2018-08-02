# -*- coding: utf-8 -*-
"""
Created on Mon Jul 02 17:21:52 2018

@author: Edward
"""

from __future__ import print_function

import numpy as np
from shapely.geometry import LineString, Point
from shapely.affinity import rotate
import cv2
import copy

def fitEllipse(points):
    (center, size, angle) = cv2.fitEllipse(np.array(points))
    return center, size, angle

"""
    Is the point inside the ellipse fit for these shapePoints?
"""
def pointInsideEllipse(shapePoints, point):
    center, size ,angle = fitEllipse(shapePoints)
    
    cos_angle = np.cos(np.radians(180.-angle))
    sin_angle = np.sin(np.radians(180.-angle))
    
    xc = point[0] - center[0]
    yc = point[1] - center[1]
    
    xct = xc * cos_angle - yc * sin_angle
    yct = xc * sin_angle + yc * cos_angle 
    
    rad_cc = (xct**2/(size[0]/2.)**2) + (yct**2/(size[1]/2.)**2)
    return rad_cc<=1

def shapelyPoint2NumpyPoint(point):
    return np.array((point.xy[0][0], point.xy[1][0]), dtype=np.float64)

"""
    Expands the ellipse fit for ellipsePoints, untill the expanded
    ellipse touches the point.
    Returns the expanded ellipse
    
    flagExpand - does it allow only to expand the shape or only to collapse it? 
"""
def expandEllipseUntillPoint(ellipsePoints, point, flagExpand=False):
    center, size, angle = fitEllipse(ellipsePoints)
    point = np.array(point, dtype=np.float64)
    center = np.array(center, dtype=np.float64)
    size = np.array(size, dtype=np.float64)
    
    """
        Return original ellipse if poin is inside it
    """
    if flagExpand:
        if pointInsideEllipse(ellipsePoints, point):
            return ellipsePoints
    else:
        if not pointInsideEllipse(ellipsePoints, point):
            return ellipsePoints
    
    """
        Find the angle with the x-axis in radians
    """
    angleRad = (90.0-angle)/360.0*2*np.pi
    
    """
        What should be the new ellipse size so that an ellipse
        of this center and angle, touches the point point?
        
        Ellipse centered at (0,0), rotated by t (your theta), has equation for x-coordinate
            x = a * cos(phi) * cos(t) + b * sin(phi) * sin(t)
    """
    point = shapelyPoint2NumpyPoint(rotate(Point(point), angle=-angleRad, use_radians=True, origin=center))
    dis = point-center
    theta = np.arctan(np.abs(dis[1]/dis[0]) * (size[0]/size[1]))
    newsize = np.abs(dis) / np.array([np.cos(theta), np.sin(theta)], dtype=np.float64)
    
    """
        Generate point for the new ellipse
    """
    newEllipsePoints = []
    for _ in range(100):
        theta = np.random.random()*4*np.pi-2*np.pi
        x = center[0] + newsize[0]*np.cos(theta)
        y = center[1] + newsize[1]*np.sin(theta)
        pt = shapelyPoint2NumpyPoint(rotate(Point((x,y)), angle=angleRad, use_radians=True, origin=center))
        newEllipsePoints.append(pt)
    return np.array(newEllipsePoints, dtype=np.int64)