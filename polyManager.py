# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 18:08:53 2018

@author: Edward
"""

import numpy as np
from matplotlib import pyplot as plt
import cv2
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import os
import csv
from lineManager import lineMgr
from commonFunctions import distance, extendList

def drawLine(pic,pt1,pt2,rgb=(255,255,255)):
    cv2.line(pic, (pt1[1],pt1[0]), (pt2[1],pt2[0]), rgb)
    
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

"""
    This class manager several polygons in an image
"""
class PolyManager:
    def __init__(self):
        self.polygonsList = []
        self.polyPoints = []
        self.gDataDir = None
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.polyMaskList = []
        self.polyMaskPointsList = []
        self.polyIntensities = []
    
    def addPolyPoint(self, point):
        self.polyPoints.append(np.array(point,dtype=int))
        
    def removePolyPoint(self, location):
        for i in range(0,len(self.polyPoints)):
            if i>=len(self.polyPoints):
                break;
            if distance(self.polyPoints[i],location)<=10:
                del self.polyPoints[i];
        pass;
        
    def clearCurrentPoly(self):
        self.polyPoints = []
        
    """
        Close the polygon by making the first point also the last point
    """
    def closePoly(self):
        if len(self.polyPoints)>1:
            self.addPolyPoint(self.polyPoints[0])
            
    """
        Returns the polygon the user is working on right now
    """
    def getCurrentPoly(self):
        return self.polyPoints

    def addPolygon(self, points):
        self.polygonsList.append(points)
        
    """
        Remove the last (added) polygon
    """
    def removeLastPolygon(self):
        del self.polygonsList[-1]
        
    """
        Remove all polygons that the point falls inside.
    """
    def removePolygon(self, point):
        for i in range(0,len(self.polygonsList)):
            if i>=len(self.polygonsList):
                break
                
            polygon = Polygon(self.polygonsList[i]);
            if polygon.contains(Point(point[0],point[1])):
                del self.polygonsList[i]
                i = i-1
    
    def showAllPolygons(self, img):
        for i in range(len(self.polygonsList)):
            self.showPolygon(img, self.polygonsList[i], i)
            
        # Show the one we are working on right now
        self.showPolygon(img, self.polyPoints, len(self.polygonsList))
        
    def showPolygon(self, img ,polyPoints, index): 
        if len(polyPoints)==0:
            return
        
        # Draw the lines
        prevPt = None
        for pt in polyPoints:
            if prevPt is not None:
                drawLine(img,prevPt,pt)
            prevPt = pt
            
        # Draw the rectangles
        for pt in polyPoints:
            drawRect(img,pt[0],pt[1],L=2)
            
        # Draw the circle number
        cv2.putText(img,'#'+str(index),(polyPoints[0][1]+10,polyPoints[0][0]), self.font, 0.5,(100,255,0),1)

    """
        Return the area of the current / last polygon. This area depends on the factor
        of by how much the pixels were inflated (hight and width was multiplied by).
        
        The area returned is in [pixel * pixel] units.
    """
    def getPolyArea(self, factor):
        x = np.array([pt[0] for pt in self.polygonsList[-1]],dtype=float)
        y = np.array([pt[1] for pt in self.polygonsList[-1]],dtype=float)
        x = x * 1/factor
        y = y * 1/factor
        return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

    def measureAveragePolyIntensity(self, grayImg, img, frame, polyPoints, index):
        global polyMaskList,polyMaskPointsList;#polyPoints,polyMask,polyMaskPoints;
        
        if len(polyPoints)<2:
            return;
        
        flagMask = False;
        if len(self.polyMaskPointsList)>index and len(self.polyMaskList)>index:
            if np.array_equal(np.array(polyPoints),np.array(self.polyMaskPointsList[index])):
                mask = self.polyMaskList[index];
                flagMask = True;
        if flagMask==False:
            mask = np.array(grayImg,dtype=bool);
            mask[:] = False;
            
            xpoints = [pt[0] for pt in polyPoints];
            ypoints = [pt[1] for pt in polyPoints];
            xmin = np.min(xpoints);
            xmax = np.max(xpoints);
            ymin = np.min(ypoints);
            ymax = np.max(ypoints);
            
            polygon = Polygon(polyPoints);
            for x in range(xmin,xmax+1):
                for y in range(ymin,ymax+1):
                    if polygon.contains(Point(x, y)):
                        mask[x,y] = True;
            
            self.polyMaskList = extendList(self.polyMaskList,index);
            self.polyMaskList[index] = mask;
            self.polyMaskPointsList = extendList(self.polyMaskPointsList,index);
            self.polyMaskPointsList[index] = np.copy(polyPoints);
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
        for i in range(0,len(self.polygonsList)):
            #measureAveragePolyIntensity(grayImg,img,frame,polygonsList[i],i);
            selectedPixels = []
            selectedPixelsCoord = []
            linePoints = []
            for j in range(0,len(self.polygonsList[i])-1):
                selectedPixelsNew,selectedPixelsCoordNew = lineMgr.measureIntensityForLine(grayImg,img,frame,self.polygonsList[i][j],self.polygonsList[i][j+1],j)
                #print('selectedPixelsCoordNew: ',selectedPixelsCoordNew)
                if len(selectedPixels)==0:
                    selectedPixels = np.array(selectedPixelsNew);
                    selectedPixelsCoord = np.array(selectedPixelsCoordNew)
                    #linePoints = np.array([polygonsList[i][j]])
                else:
                    selectedPixels = np.concatenate((selectedPixels,selectedPixelsNew))
                    selectedPixelsCoord = np.concatenate((selectedPixelsCoord,selectedPixelsCoordNew))
                    #linePoints = np.concatenate(linePoints,np.array([polygonsList[i][j]]))
            linePoints = np.array(self.polygonsList[i])
            if self.gDataDir is None:
                folderNum = 0
                
                if os.path.exists('selectedPixels/'+str(folderNum)):
                    print('Checking for folder: '+'selectedPixels/'+str(folderNum)+' = folder exists')
                    folderNum = folderNum + 1
                dataDir = 'selectedPixels/'+str(folderNum)
                print('Creating folder: '+dataDir)
                
                #cwd = os.getcwd()
                #print('cwd = ',cwd)
                #os.sys.exit()
                
                while True:
                    try:
                        os.mkdir(dataDir) 
                    except:
                        folderNum = folderNum + 1
                        dataDir = 'selectedPixels/'+str(folderNum)
                        continue
                    break
                self.gDataDir = dataDir
                print('Folder created!')
            
            # Save plot
            fig = plt.figure(100)
            plt.plot(range(0,len(selectedPixels)),selectedPixels)
            fig.savefig(self.gDataDir+'/selectedPixels['+str(frame)+'].png')
            fig.clf();
            plt.close(fig);
            
            # Save data
            np.save(self.gDataDir+'/selectedPixels['+str(frame)+']',selectedPixels)
            
            # Save line pts
            if os.path.exists(self.gDataDir+'/selectedPixels[points]')==False:
                np.save(self.gDataDir+'/selectedPixels[points]',linePoints)
            
            # Save coordinates for line
            if os.path.exists(self.gDataDir+'/selectedPixels[coord]')==False:
                np.save(self.gDataDir+'/selectedPixels[coord]',selectedPixelsCoord)
    
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
                fig.savefig(self.gDataDir+'/pixelsCoord.png')
                fig.clf()
                plt.close(fig)
                
                