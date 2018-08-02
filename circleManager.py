# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 18:08:31 2018

@author: Edward
"""

import numpy as np
from matplotlib import pyplot as plt
import cv2

def extendList(l,i,j=None,k=None):
    while len(l)<i+1:
        l.append([])
    if j is not None:
        while len(l[i])<j+1:
            l[i].append([])
            if k is not None:
                while len(l[i][j])<k+1:
                    l[i][j].append([])
    return l

def drawCircle(pic, x, y, r, rgb=(255,255,255)):
    cv2.circle(pic,(y,x),np.int(r),rgb)

"""
    Gives the distance between 2 points
"""
def distance(pt1,pt2):
    return ((pt1[0]-pt2[0])**2+(pt1[1]-pt2[1])**2)**0.5

"""
    This class manager several circles in an image
"""
class CircleManager:
    def __init__(self):
        self.circleIntensities = []
        self.circleRgbList = []
        self.circlePtList = []
        self.circleRList = []
        self.avgCircleIntenistyList = []
        self.circleMasks = []
        self.circleMasksData = []
        
    def addCircleIntensity(index,frame,avgIntensity):
        self.circleIntensities = extendList(self.circleIntensities,index)
        self.circleIntensities[index] = extendList(self.circleIntensities[index],frame)
        self.circleIntensities[index][frame] = avgIntensity
        
    def addCircle(self, point,r,rgb=(255,255,255)):
        self.circlePtList.append(point)
        self.circleRgbList.append(rgb)
        self.circleRList.append(r)
    
    """
        Remove all circles that the point falls inside.
    """
    def removeCircle(self, point):
        for i in range(0,len(self.circlePtList)):
            if i>=len(self.circlePtList):
                break
            if distance(self.circlePtList[i],point)<=self.circleRList[i]:
                del self.circlePtList[i]
                del self.circleRgbList[i]
                del self.circleRList[i]
                self.removeCircleFromIntensities(i)
                
    def showAllCircles(self, img):
        font = cv2.FONT_HERSHEY_SIMPLEX; 
        
        for i in range(0,len(self.circlePtList)):
            # Draw the circle itself
            drawCircle(img,self.circlePtList[i][0],self.circlePtList[i][1],self.circleRList[i],self.circleRgbList[i]);
            # Draw the circle number
            cv2.putText(img,'#'+str(i),(self.circlePtList[i][1],self.circlePtList[i][0]), font, 0.5,(100,255,0),1);
                
    def removeCircleFromIntensities(self, index):
        if len(self.circleIntensities)>=index+1:
            del self.circleIntensities[index]
    
    def measureAverageCircleIntensityForAllCircles(self, grayImg, img, frame):
        for i in range(0,len(self.circlePtList)):
            avgIntensity = self.measureAverageCircleIntensity(grayImg,img,self.circlePtList[i],self.circleRList[i],i);
            self.addCircleIntensity(i,frame,avgIntensity);
            #avgCircleIntenistyList = extendList(avgCircleIntenistyList,i);
            #avgCircleIntenistyList[i].append(avgIntensity);
    
    """
        Measures the average pixel intensity inside the cirle located at point with
        radius r.
    """
    def measureAverageCircleIntensity(self, grayImg, img, point, r, index):
        r = np.int(r)
        
        """
        s1 = time.time();
        sumIntensity = 0;
        n = 0;
        for x in range(-r,r+1):
            for y in range(-r,r+1):
                if vec_length([x,y])<=r and point[0]+x>=0 and point[1]+y>-0 \
                    and point[0]+x<grayImg.shape[0] and point[0]+y<grayImg.shape[1]:
                        #mask[point[0]+x,point[1]+y] = True;
                        sumIntensity += grayImg[point[0]+x,point[1]+y];
                        n += 1;
        t1 = time.time()-s1;
        print('Avg intenisty method 1 = ',sumIntensity/n);
        
        s1 = time.time();
        sumIntensity = 0;
        n = 0;
        for x in range(point[0]-r,point[0]+1):
            for y in range(point[1]-r,point[1]+1):
                if ((x - point[0])*(x - point[0]) + (y - point[1])*(y - point[1]) <= r*r):
                    xSym = point[0] - (x - point[0]);
                    ySym = point[1] - (y - point[1]);
                    
                    # (x, y), (x, ySym), (xSym , y), (xSym, ySym) are in the circle
                    sumIntensity += grayImg[x,y] + grayImg[x,ySym] + grayImg[xSym,y] + grayImg[xSym,ySym];
                    n += 4;
                    
                    #mask[point[0]+x,point[1]+y] = True;
        t2 = time.time()-s1;
        print('Avg intenisty method 2 = ',sumIntensity/n);
        """
        
        #s1 = time.time();
        ##
        ## This method gives the closest results to method 1 and it the fastest
        #########################################################################
        
        if len(self.circleMasks)<index+1:
            mask = np.array(grayImg,dtype=bool)
            mask[:] = False
            for x in range(point[0]-r,point[0]+1):
                for y in range(point[1]-r,point[1]+1):
                    if ((x - point[0])*(x - point[0]) + (y - point[1])*(y - point[1]) <= r*r):
                        xSym = point[0] - (x - point[0])
                        ySym = point[1] - (y - point[1])
                        
                        #
                        # (x, y), (x, ySym), (xSym , y), (xSym, ySym) are in the circle
                        ###################################################################
                        
                        #sumIntensity += grayImg[x,y] + grayImg[x,ySym] + grayImg[xSym,y] + grayImg[xSym,ySym];
                        #n += 4;
                        
                        if x>=0 and x<mask.shape[0] and y>=0 and y<mask.shape[1]:
                            mask[x,y] = True
                            if ySym>=0 and ySym<mask.shape[1]:
                                mask[x,ySym] = True
                            if xSym>=0 and xSym<mask.shape[0]:
                                mask[xSym,y] = True
                        if ySym>=0 and ySym<mask.shape[1] and xSym<mask.shape[1] and xSym>=0:
                            mask[xSym,ySym] = True
            self.circleMasks = extendList(self.circleMasks,index)
            self.circleMasksData = extendList(self.circleMasksData,index)
            self.circleMasks[index] = mask
            self.circleMasksData[index] = (point,r)
        elif np.array_equal(self.circleMasksData[index][0],point) or self.circleMasksData[index][1]!=r:
            #print('circleMasksData[index]=',circleMasksData[index]);
            #print('point = ',point);
            #print('r=',r);
                    
            mask = np.array(grayImg,dtype=bool)
            mask[:] = False
            for x in range(point[0]-r,point[0]+1):
                for y in range(point[1]-r,point[1]+1):
                    if ((x - point[0])*(x - point[0]) + (y - point[1])*(y - point[1]) <= r*r):
                        xSym = point[0] - (x - point[0])
                        ySym = point[1] - (y - point[1])
                        
                        #
                        # (x, y), (x, ySym), (xSym , y), (xSym, ySym) are in the circle
                        ###################################################################
                        
                        #sumIntensity += grayImg[x,y] + grayImg[x,ySym] + grayImg[xSym,y] + grayImg[xSym,ySym];
                        #n += 4;
                        
                        if x>=0 and x<mask.shape[0] and y>=0 and y<mask.shape[1]:
                            mask[x,y] = True
                            if ySym>=0 and ySym<mask.shape[1]:
                                mask[x,ySym] = True
                            if xSym>=0 and xSym<mask.shape[0]:
                                mask[xSym,y] = True
                        if ySym>=0 and ySym<mask.shape[1] and xSym<mask.shape[1] and xSym>=0:
                            mask[xSym,ySym] = True
            self.circleMasks[index] = mask
            self.circleMasksData[index] = (point,r)
        else:
            #print('Circle mask fit found');
            mask = self.circleMasks[index]
        avgIntensity = np.mean(grayImg[mask])

        return avgIntensity
    
    def saveCircleIntensities(self, filename):        
        if filename is not None:    
            csvOutputFile = filename + "circleIntensities.csv"
        else:
            csvOutputFile = "circleIntensities.csv"
            
        # In case we didn't start at the first frame
        for i in range(0,len(self.circleIntensities)):
            for frame in range(0,len(self.circleIntensities[i])):
                if self.circleIntensities[i][frame]==[]:
                    self.circleIntensities[i][frame] = -1
        
        for i in range(0,len(self.circleIntensities)):
            #
            # Output graph
            ##########################################
            fig = plt.figure(100)
            plt.plot(range(0,len(self.circleIntensities[i])),self.circleIntensities[i],'b')
            plt.xlabel('time [frame]')
            plt.ylabel('Circle Average Intenisty')
            plt.title('Circle Average Intensity as a Function of Time')
            fig.savefig(filename+"cirlceIntenistyPlot["+str(i)+"].jpeg")
            fig.clf()
            plt.close(fig)
                
                
        #
        # Output to *.CSV
        ##########################################
        if len(self.circleIntensities)>0:
            print('Writing to CSV file: ',csvOutputFile)
            with open(csvOutputFile, 'w') as csvfile:
                writer = csv.writer(csvfile, delimiter=',',\
                    quotechar='|', quoting=csv.QUOTE_MINIMAL,lineterminator='\n')
                
                # Write header row
                row1 = ['Frame #']
                for i in range(0,len(self.circleIntensities)):
                    row1.append('Circle '+str(i))
                writer.writerow(row1)
                    
                # Write data rows
                rows = []
                for frame in range(0,len(self.circleIntensities[0])):
                    row = []
                    row.append(str(frame));
                    for i in range(0,len(self.circleIntensities)):
                        if self.circleIntensities[i][frame]==-1:
                            row.append("")
                        else:
                            row.append(str(self.circleIntensities[i][frame]))
                    rows.append(row)
                                    
                for i in range(0,len(rows)):
                    writer.writerow(rows[i])
          
    def clearCircleIntensities(self):
        self.circleIntensities = []
    
"""
    This class manages a drawin for a single circle in an image
"""
class SingleCircleDrawingManager:
    def __init__(self):
         self.circleRgb = None  # the color of the cirlc
         self.circlePt = None   # the point of the center
         self.circleR = None    # the radius
         self.circleOn = False  # is the circle showing in the image

    def enableCircle(self, point, r, rgb=(255,255,255)):
        self.circleOn = True
        self.circleRgb = rgb
        self.circlePt = point
        self.circleR = r
        
    def showCircle(self, img):
        if self.circleOn:
            drawCircle(img,self.circlePt[0],self.circlePt[1],self.circleR,self.circleRgb)
            
    def disableCircle(self):
        self.circleOn = False
    
    def getCircleState(self):
        return self.circleOn
        
    def getCircle(self):
        return self.circlePt, self.circleR
        
    def setCenter(self, point):
        self.circlePt = point
        
    def getCenter(self):
        return self.circlePt
    