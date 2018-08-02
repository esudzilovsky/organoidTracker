# -*- coding: utf-8 -*-
"""
Created on Mon Jul 02 16:00:02 2018

@author: Edward
"""

import numpy as np
from shapely.geometry import LineString, Point
import copy

def norm(point):
    return np.sqrt(np.sum(np.power(point,2)))

def getPolygonCenter(points):
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
    return centeroid / (6.0*signedArea)

def distanceLine2Point(points, point):
    points = np.array(points, dtype=np.float64)
    point = np.array(point, dtype=np.float64)
    return LineString(points).distance(Point(point))

def distancePolygon2Point(points, point):
    if np.all(points[0]==points[-1]):
        size = len(points)-1
    else:
        size = len(points)
    distances = []
    for i in range(size):
        if i==len(points)-1:
            j = 0
        else:
            j = i+1
        line = [points[i], points[j]]
        distances.append(distanceLine2Point(line, point))
        
    minDistance = np.min(distances)
    
    return minDistance

"""
    Returns:
        1. The distance from the point which is at the intersection
            of the line connecting the center of a polygon to an extrnal point,
            and one of the polygons borders, to the external point of the polygon.
        2. The distance from the intersection and the center of the polygon.
"""
def distancePolygon2ExternalPointAndCenter(points, point):
    if np.all(points[0]==points[-1]):
        size = len(points)-1
    else:
        size = len(points)
        
    polyCenter = getPolygonCenter(points)
    #arrow = (point-polyCenter)*10000
    lineCenterPoint = np.array([polyCenter, point],dtype=np.float64)
    #lineCenterPoint = np.array([polyCenter, polyCenter+arrow],dtype=np.float64)
    
    minDistance = None
    for i in range(size):
        if i==len(points)-1:
            j = 0
        else:
            j = i+1
        line = [points[i], points[j]]
        intersection = LineString(lineCenterPoint).intersection(LineString(line))
        dis = intersection.distance(Point(point))
        if dis>0:
            intersectionPt = np.array([intersection.xy[0][0],intersection.xy[1][0]], dtype=int)
            minDistance = dis
            centerDistance = norm(intersectionPt-polyCenter)
            break
    """
        This means the point is inside the shape, not outside of it.
    """
    if minDistance is None:
        return None, None
    return minDistance, centerDistance

"""
    Returns:
        1. The distance from a point internal to the polyogn and the polygons
            center.
        2. The distance from the point which is at the intersection
            of the line connecting the center of a polygon to an internal point,
            and the polygons center.
"""
def distancePolygon2InternalPointAndCenter(points, point):
    if np.all(points[0]==points[-1]):
        size = len(points)-1
    else:
        size = len(points)
        
    polyCenter = getPolygonCenter(points)
    arrow = (point-polyCenter)*10000
    lineCenterPoint = np.array([polyCenter, polyCenter+arrow],dtype=np.float64)
    
    point2Center = norm(point - polyCenter)
    for i in range(size):
        if i==len(points)-1:
            j = 0
        else:
            j = i+1
        line = [points[i], points[j]]
        intersection = LineString(lineCenterPoint).intersection(LineString(line))
        dis = intersection.distance(Point(point))
        if dis>0:
            intersectionPt = np.array([intersection.xy[0][0],intersection.xy[1][0]], dtype=int)
            centerDistance = norm(intersectionPt-polyCenter)
            break
    """
        This means the point is inside the shape, not outside of it.
    """
    if point2Center is None:
        return None, None
    return point2Center, centerDistance

"""
    Expands the polygon by a factor.
    Returns the expanded polygon (integer points).
"""
def expandPoly(points, factor):
    points = np.array(points, dtype=np.float64)
    expandedPoly = points*factor
    expandedPoly -= getPolygonCenter(expandedPoly)
    expandedPoly += getPolygonCenter(points)
    return np.array(expandedPoly, dtype=np.int64)

"""
    Expands the polygon untill one of the borders touches the point.
    Returns the expanded polygon.
    
    flagExpand - does it allow only to expand the shape or only to collapse it? 
"""
def expandPolyUntillPoint(points, point, flagExpand=False):
    minDistance, intersection2CenterDistance = distancePolygon2ExternalPointAndCenter(points, point)
    
    if flagExpand:
        """
            The point is inside the shape, cannot exapnd!
        """
        if minDistance is None:
            return copy.deepcopy(points)
        return expandPoly(points, 1+minDistance/intersection2CenterDistance)
    else:
        if minDistance is not None:
            return copy.deepcopy(points)
        point2Center, intersection2CenterDistance = distancePolygon2InternalPointAndCenter(points, point)
        return expandPoly(points, point2Center/intersection2CenterDistance)