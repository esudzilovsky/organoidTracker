# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:22:02 2018

@author: Edward
"""

import numpy as np
from commonFunctions import extendList

def xiaoline(x0, y0, x1, y1):
    x=[]
    y=[]
    dx = x1-x0
    dy = y1-y0
    steep = abs(dx) < abs(dy)

    if steep:
        x0,y0 = y0,x0
        x1,y1 = y1,x1
        dy,dx = dx,dy

    if x0 > x1:
        x0,x1 = x1,x0
        y0,y1 = y1,y0

    gradient = float(dy) / float(dx)  # slope

    """ handle first endpoint """
    xend = round(x0)
    yend = y0 + gradient * (xend - x0)
    xpxl0 = int(xend)
    ypxl0 = int(yend)
    x.append(xpxl0)
    y.append(ypxl0) 
    x.append(xpxl0)
    y.append(ypxl0+1)
    intery = yend + gradient

    """ handles the second point """
    xend = round (x1);
    yend = y1 + gradient * (xend - x1);
    xpxl1 = int(xend)
    ypxl1 = int (yend)
    x.append(xpxl1)
    y.append(ypxl1) 
    x.append(xpxl1)
    y.append(ypxl1 + 1)

    """ main loop """
    for px in range(xpxl0 + 1 , xpxl1):
        x.append(px)
        y.append(int(intery))
        x.append(px)
        y.append(int(intery) + 1)
        intery = intery + gradient;

    if steep:
        y,x = x,y

    coords=zip(x,y)

    return coords

"""
    This class manager several lines in an image
"""
class LineManager:
    def __init__(self):
        self.lineMaskList = []
        self.lineMaskPointsList = []
        self.lineCoordsList = []
        self.linePoints = None
        self.lineOn = False
        
    def measureIntensityForLine(self, grayImg, img, frame, ptA, ptB, index):
        global lineMaskList,lineMaskPointsList,lineCoordsList
        
        flagMask = False;
        if len(self.lineMaskPointsList)>index and len(self.lineMaskList)>index:
            if np.array_equal(np.array((ptA,ptB)),np.array(self.lineMaskPointsList[index])):
                mask = self.lineMaskList[index]
                lineCoords = self.lineCoordsList[index]
                flagMask = True
        if flagMask==False:
            """
            minX,maxX = np.min([ptA[0],ptB[0]]), np.max([ptA[0],ptB[0]]);
            minY,maxY = np.min([ptA[1],ptB[1]]), np.max([ptA[1],ptB[1]]);
            
            for x in range(minX,maxX+1):
                for y in range(minY,maxY+1):
                    if matplotlib.path.Path([ptA,ptB]).contains_points([(x,y)]):
                        img[y,x] = (0,0,255);
            """
            mask = np.array(grayImg,dtype=bool)
            mask[:] = False
            
            coord = xiaoline(ptA[0],ptA[1],ptB[0],ptB[1])
            lineCoords = []
            for c in coord:
                mask[c] = True;
                lineCoords.append(c)
            #lineCoords = coord
                
            self.lineMaskList = extendList(self.lineMaskList,index)
            self.lineMaskList[index] = mask
            self.lineMaskPointsList = extendList(self.lineMaskPointsList,index)
            self.lineMaskPointsList[index] = np.copy((ptA,ptB))
            self.lineCoordsList = extendList(self.lineCoordsList,index)
            self.lineCoordsList[index] = lineCoords
        selectedPixels = grayImg[mask]
        return selectedPixels,lineCoords
    
    def enableLine(pointA,pointB):
        global linePoints,lineOn;
        linePoints = (pointA,pointB)
        lineOn = True
    
    def disableLine():
        global linePoints,lineOn
        lineOn = False
        linePoints = None
        
    linesPointsList = [];
    def addLine(pointA,pointB):
        global linesPointsList;
        linesPointsList.append((pointA,pointB));
        #pass;
    
    def showLine(img,pointA,pointB):
        # Draw the line
        drawLine(img,pointA,pointB);
        
    def showAllLines(img):
        global linesPointsList;
        global linePoints,lineOn;
        
        if lineOn:
            showLine(img,linePoints[0],linePoints[1]);
        
        for points in linesPointsList:
            showLine(img,points[0],points[1]);
        
    def measureIntensityForAllLines(grayImg,img,frame):
        global linesPointsList
        for i in range(0,len(linesPointsList)):
            measureIntensityForLine(grayImg,img,frame,linesPointsList[i][0],linesPointsList[i][1],i)
    
    def getLineWidth(x,y,a):
        return np.max(distancePointToLine(x,y,a[0],-1,a[1]))
    
    def distancePointToLine(x,y,a,b,c):
        return np.abs(a*x+b*y+c)/np.power(np.power(a,2)+np.power(b,2),0.5)
    
lineMgr = LineManager()