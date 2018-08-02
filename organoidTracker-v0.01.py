# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 22:11:43 2017

@author: Edward
"""
from __future__ import print_function

import os
import time
import numpy as np
import cv2
"""
from scipy import ndimage as ndi
from scipy import ndimage
from scipy import interpolate
from scipy.interpolate import interp1d
"""
import sys

#from matplotlib import pyplot as plt

#from lineManager import lineMgr
from circleManager import CircleManager, SingleCircleDrawingManager
from pointsManager import PointsManager
from messageBox import inputFileMBox
from mouseControl import MouseControl
from frameControl import FrameControl

currentFrameNum = -1       # Frame number (starting from 1)
frameID = None

# 1 - video
# 2 - curves
# 3 - laser
buttonMode = 1
        
textLineHeight = 20
nextTextLineY = textLineHeight*2
font = cv2.FONT_HERSHEY_SIMPLEX
def writeInformationText(img):
    global textLineHeight,nextTextLineY,font
    # Write some Text
    
    linesInfo = ["c - Close poly","r - Remove last shape","Mouse left button: add point","Mouse right button: remove point/poly/circle"];
    #cv2.putText(img,"-- Mode 3 --",(10,textLineHeight), font, 0.5,(255,255,255),1)    
    nextTextLineY = textLineHeight*1;    
    for i in range(0,len(linesInfo)):
        cv2.putText(img,linesInfo[i],(10,nextTextLineY+textLineHeight*i), font, 0.5,(255,255,255),2);
    nextTextLineY += textLineHeight*(1+np.max([len(linesInfo)]));
    
"""
    This is called whenever the fame is changed, but we don't know
    if it is the next frame, previous frame, or a reset!
"""
def newFrame():
    pass
    
VIDEO_FILE_MODE2 = inputFileMBox("organoidTracker.config", None, None)

"""
    Frame ctrl
"""
frameCtrl = FrameControl()
frameCtrl.setInputVideo(VIDEO_FILE_MODE2)
totNumFrames = frameCtrl.getTotalFrameCount()
print('Tot frame #: '+np.str(totNumFrames))

"""
    Managers and controllers
"""
circlesMgr = CircleManager()
circleDrawingMgr = SingleCircleDrawingManager()
shapeMgr = PointsManager(totNumFrames, 0)
mouseCtrl = MouseControl(circlesMgr, circleDrawingMgr, shapeMgr)

if True:
    lastFrameDrawingTime = time.time()
    
    flagReset = False          # Reset video in mode2
    flagFirstOpen = True
    isPaused = False
    flagOneFrame = False
    flagOneFrameBack = False

    prevFrameID = -1
    prevThreshold = -1
    
    prevTime = time.time()          # The last time a button was pressed
    buttonMode = 2                  # The mode for button meaning, default = video    
    factor = 1.5                    # The factor for rezing the frame, or zooming in
    
    #
    ## Mode 3 settings
    #################################
    mode = 3
    isPaused = True
    circleIntensitiesSaved = True
    
    flagOneFrameForward = True
    flagOneFrameBack = False
    
    while(frameCtrl.isRunning()):
        if flagFirstOpen==True:
            cv2.namedWindow('frame')
            cv2.setMouseCallback('frame', mouseCtrl.callback)
            flagFirstOpen = False
        
        # Show frame after cuve additions
        circleIntensity = None
        if flagOneFrameForward==True or flagOneFrameBack==True or flagReset==True:
            if flagReset==True:
                frameCtrl.resetVideo()
                flagReset = False
            if flagOneFrameForward==True:
                # Measure in frame 1 before moving to frame 2
                if currentFrameNum==1:
                    grayFrame = frameCtrl.getCurrentGrayFrame()
                    
                    # Measure avg intensity for all circles
                    circlesMgr.measureAverageCircleIntensityForAllCircles(grayFrame,frameCtrl.getCurrentFrame(),currentFrameNum-1)
                        
                    # Measure avg intensity for the polygon
                    shapeMgr.measureAveragePolyIntensityForAllPolys(grayFrame,frameCtrl.getCurrentFrame(),currentFrameNum-1)
                    
                # Load new frame
                #print('frameCtrl.forward()')
                frameCtrl.forward()
                
                # If we passed the last frame, get back to the first one
                if frameCtrl.getCurrentFrame() is None:
                    frameCtrl.backward()
                    
                    # Save intensities here?
                
            if flagOneFrameBack==True:
                frameCtrl.backward()
                
                # Have we gone too far back?
                if frameCtrl.getCurrentFrame() is None:
                    frameCtrl.forward()
                
                flagOneFrameBack = False
            
            currentFrameNum = frameCtrl.getCurrentFrameNumber()
            if currentFrameNum==1:
                circleIntensitiesSaved = False;
                
            # Resize the frame or zoom in
            width   = frameCtrl.getFrameWidth()
            height  = frameCtrl.getFrameHeight()
            grayFrame = frameCtrl.getCurrentGrayFrame()
            
            if flagOneFrameForward==True:
                if isPaused==True:
                    flagOneFrameForward = False;
                else:
                    if circleIntensitiesSaved==False:                                
                        # Measure avg intensity for all circles
                        circlesMgr.measureAverageCircleIntensityForAllCircles(grayFrame,frameCtrl.getCurrentFrame(),frameCtrl.getCurrentFrameNumber()-1);
                        
                        # Measure avg intensity for the polygon
                        shapeMgr.measureAveragePolyIntensityForAllPolys(grayFrame,frameCtrl.getCurrentFrame(),frameCtrl.getCurrentFrameNumber()-1);

                    
            # Write button information
            writeInformationText(frameCtrl.getCurrentFrame())
                
            # Send new frame # to shapeMgr
            shapeMgr.setCurrentFrame(frameCtrl.getCurrentFrameNumber()-1)
                    
            # Start our frame from the base frame
            img_ch1_draw = np.copy(frameCtrl.getCurrentFrame())
            
            # Draw frame number
            cv2.putText(img_ch1_draw,"Frame: "+str(frameCtrl.getCurrentFrameNumber()),(10,nextTextLineY+textLineHeight), font, 0.5,(255,255,255),2);
            if circleIntensity is not None:
                cv2.putText(img_ch1_draw,"Circle intenisty: "+str(circleIntensity),(10,nextTextLineY+textLineHeight*2), font, 0.5,(0,0,200),2);
            
            if buttonMode==1:
                # Show current circle
                circleDrawingMgr.showCircle(img_ch1_draw)
                
                # Show all circles
                circlesMgr.showAllCircles(img_ch1_draw)
            elif buttonMode==2:
                # Show polygons / shapes
                shapeMgr.showAllShapes(img_ch1_draw)
            
            elapsed = time.time()-lastFrameDrawingTime
            if True:#elapsed>0.5:
                #print('showing frame')
                cv2.imshow("frame", img_ch1_draw)
                lastFrameDrawingTime = time.time()
            pass;
            
        key = cv2.waitKey(100)
        
        # Reset it
        if key&0xFF == ord('r'):
            flagReset = True;
            isPaused = True
            flagOneFrameForward = False
            
            # Remove last polygon
            shapeMgr.removeLastShape()
        
        # Button mode - curves
        if key&0xFF == ord('c'):
            if mode==3 and buttonMode==2:
                """
                polyMgr.closePoly()
                polyMgr.addPolygon(polyMgr.getCurrentPoly())
                """
                if shapeMgr.shapeType(shapeMgr.getCurrentShape())=='polygon':
                    shapeMgr.closePoly()
                shapeMgr.addShape(shapeMgr.getCurrentShape())
                shapeMgr.clearCurrentShape()
                editingPoly = False
                
                a = shapeMgr.getPolyArea(factor)
                print('Poly area = ',np.round(a,3))
            continue;
        
        # Quit
        if (key&0xFF == ord('q')) or (key&0xFF == ord('Q')):
            break;
            
        # Mode=2, Saving the curve fit
        if key&0xFF == ord('s'):
            continue
        
        # Paused
        if key&0xFF == ord(' '):
            if mode==2 and buttonMode==2:
                pass
            if mode==2 and buttonMode==3:
                pass
            if mode==3:
                isPaused = not isPaused;
                if isPaused==False:
                    flagOneFrameForward = True
            continue
        
        # Set threshold
        if key&0xFF == ord('v'):
            if mode==1:
                #gThreshold = np.float(mbox("Enter the thereshold:", entry=True));
                #print('threshold=',threshold);
                pass
            if mode==2:
                buttonMode = 1
                mouseCtrl.setButtonMode(1)
            continue
            
        thisTime = time.time()
        #print('thisTime-prevTime=',thisTime-prevTime);

        # One frame (right arrow)     
        if int(key) == 2555904:
            # Move to next frame in mode==2
            if (mode==2 and buttonMode==1)  or mode==3:
                flagOneFrameForward = True
                pass
            # Move to next frame in mode==1
            if mode==1:
                flagOneFrame = True
                isPaused = True
            continue
            
        # One frame (left arrow)
        if int(key) == 2424832:
            # Move to previous frame in mode==2
            if (mode==2 and buttonMode==1) or mode==3:
                flagOneFrameBack = True
                pass
            # Move to previous frame in mode==1
            if mode==1:            
                flagOneFrameBack = True
                isPaused = True
            continue
            
        # Up arrow
        if int(key) == 2490368:                                  
            continue
            
        # Down arrow
        if int(key) == 2621440:
            continue
            
        if key&0xFF == ord('-'):
            if mode==1:
                pass
            continue
         
        # Save last button press time
        prevTime = time.time()

"""
    Free resources
"""
frameCtrl.release()
cv2.destroyAllWindows()