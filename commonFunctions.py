# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:50:40 2018

@author: Edward
"""

import numpy as np
import os

def extendList(l,i,j=None,k=None,o=None):
    while len(l)<i+1:
        l.append([])
    if j is not None:
        while len(l[i])<j+1:
            l[i].append([])
    if k is not None:
        while len(l[i][j])<k+1:
            l[i][j].append([])
    if o is not None:
        while len(l[i][j][k])<o+1:
            l[i][j][k].append([])
    return l

def anyNonEmpty(l):
    for i in range(len(l)):
        if len(l[i])>0:
            return True
    return False

"""
    Gives the distance between 2 points
"""
def distance(pt1,pt2):
    return ((pt1[0]-pt2[0])**2+(pt1[1]-pt2[1])**2)**0.5

"""
    Creates a folder if it doesn't already exist
"""
def createFolder(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        
def vec_length(v):
    return distance([0,0],v)

def angle(v1,v2):
    vec1 = np.array(v1);
    vec2 = np.array(v2);
    return np.arccos(np.dot(vec1,vec2)/(vec_length(vec1)*vec_length(vec2)))
    
def rotate(v, alpha):
    v = np.array(v)
    transform = np.matrix(((np.cos(alpha),-np.sin(alpha)),(np.sin(alpha),np.cos(alpha))))
    return np.array(v*transform,dtype=int)[0]

"""
    array - a boolean 2D array
    It fills in the 'False' points between true points.
"""
def fill(points, array):
    array = np.copy(array)
    
    # For each line (y) find the min x and max x
    ypoints = dict()
    for pt in points:
        if pt[1] not in ypoints:
            ypoints[pt[1]] = []
        ypoints[pt[1]].append(pt[0])
    for y in ypoints.keys():
        minx = np.min(ypoints[y])
        maxx = np.max(ypoints[y])
        
        array[minx:maxx,y] = True
    return array

"""
    array - a boolean 2D array
    return the number of 'True' points
"""
def area(array):
    return np.count_nonzero(array)
        
def drawRect(pic,x,y,rgb=(0,0,255),L=10):    
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
        
def drawDotCrosshair(pic,x,y,rgb1=(0,255,0),rgb2=(255,255,255)):
    drawCross(pic,x,y,rgb1,8)
    drawRect(pic,x,y,rgb2,1)
    
"""
    Find filename in the folderpath with the extension given.
    
    - Not sure if this is recursive on only for all the folders in the path....
    - Returns None if not found
    - If found retuns the first file path.
"""
def findFilenameFromFolder(folderpath, extension="avi"):
    if folderpath.endswith(extension):
        if os.path.exists(folderpath):
            return folderpath
        else:
            return None
    
    if folderpath.find(extension)==-1:
        if not (folderpath[-1]=='/'):
            folderpath = folderpath + "/"
        
        for root, dirs, filenames in os.walk(folderpath):
            for f in filenames:
                #  Make sure that "avi" is the file extension
                #  and not just appearing in the middle of the filename
                if f.endswith(extension):
                    return folderpath+f2
        return None
    return None