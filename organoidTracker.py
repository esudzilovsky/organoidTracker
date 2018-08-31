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
from messageBox import inputFileMBox, inputNumberMBox, boolQuestionMBox, twoOptionQuestionMBox
from mouseControl import MouseControl
from frameControl import FrameControl
from frameControlND2 import FrameControlND2
from commonFunctions import createFolder
import globalSettings

currentFrameNum = -1       # Frame number (starting from 1)
frameID = None

showTextFlag = True
        
textLineHeight = 20
nextTextLineY = textLineHeight*2
font = cv2.FONT_HERSHEY_SIMPLEX
TEXT_RGB = (243,243,21)
def writeInformationText(img, textRGB=TEXT_RGB):
    global showTextFlag
    if not showTextFlag:
        return
    
    global textLineHeight,nextTextLineY,font
    """
        You need to reverse the RGB order before sending to be drawn
    """
    textRGB = textRGB[::-1]
    # Write some Text
    
    linesInfo = ["<Tab> - toggle showing this text","<space> - Close poly / Finish shape","r - remove current points","u - undo remove","q - quit","CTRL+f - finish (save, remove backup then exit)","s - save to files","l - load from files","g - goto frame",'b - toggle setting borders','a - toggle adding border to shapes','e - export shapes to UNet',"Mouse left button: add point","Mouse right button: remove point/poly/shape"];
    #cv2.putText(img,"-- Mode 3 --",(10,textLineHeight), font, 0.5,(255,255,255),1)    
    nextTextLineY = textLineHeight*1;    
    for i in range(0,len(linesInfo)):
        cv2.putText(img,linesInfo[i],(10,nextTextLineY+textLineHeight*i), font, 0.5,textRGB,2);
    nextTextLineY += textLineHeight*(1+np.max([len(linesInfo)]));
    
"""
    This is called whenever the fame is changed, but we don't know
    if it is the next frame, previous frame, or a reset!
"""
def newFrame():
    pass

"""
    Save all work in all frames
"""
def saveAll(frameCtrl, shapeMgr, outputExcelFiles=False):
    global VIDEO_FILE_MODE2
    sourcePath = os.path.dirname(os.path.abspath(__file__))
    if not (sourcePath.endswith('/') or sourcePath.endswith('\\')):
        sourcePath += '/'
    #saveDir = frameCtrl.getVideoPath() + frameCtrl.getVideoBasename() + '_tracking/'
    saveDir = sourcePath + 'tracking/' + frameCtrl.getVideoBasename() + '_tracking/'
    createFolder(sourcePath + 'tracking/')
    try:
        shapeMgr.saveShapes(saveDir + 'shapes')
        if outputExcelFiles:
            shapeMgr.saveShapeAreas(saveDir + 'shapesArea', saveDir + 'shapesArea')
    except Exception as e:
        print('Could not save!')
        globalSettings.logError()
        
        """
            Pop up a message asking if to load from backup
        """
        if boolQuestionMBox("Unable to save.\rLoad from backup?"):
            shapeMgr.setTrackingDirectory(saveDir)
            shapeMgr.loadBackup()
            
            frameCtrl.saveFrameSkip(VIDEO_FILE_MODE2)
            return False
    frameCtrl.saveFrameSkip(VIDEO_FILE_MODE2)
    return True
    
def loadAll(shapeMgr):
    sourcePath = os.path.dirname(os.path.abspath(__file__))
    if not (sourcePath.endswith('/') or sourcePath.endswith('\\')):
        sourcePath += '/'
    #loadDir = frameCtrl.getVideoPath() + frameCtrl.getVideoBasename() + '_tracking/'
    loadDir = sourcePath + 'tracking/' + frameCtrl.getVideoBasename() + '_tracking/'
    #print('loadDir: '+loadDir)
    
    flagException = False
    flagLoaded = False
    try:
        flagLoaded = shapeMgr.loadShapes(loadDir, loadDir + 'shapes.npy')
    except Exception as e:
        print('Could not load!')
        globalSettings.logError()
        flagException = True
    
    if flagLoaded==False or flagException==True:
        """
            Pop up a message asking if to load from backup
        """
        if boolQuestionMBox("Unable to load.\rLoad from backup?"):
            shapeMgr.setTrackingDirectory(loadDir)
            shapeMgr.loadBackup()
VIDEO_FILE_MODE2 = inputFileMBox("organoidTracker.config", None, None)
"""
    Frame ctrl
"""
if VIDEO_FILE_MODE2.endswith('avi'):
    frameCtrl = FrameControl()
elif VIDEO_FILE_MODE2.endswith('nd2') or os.path.isdir(VIDEO_FILE_MODE2):
    frameCtrl = FrameControlND2()
else:
    print('Error: file is not a folder / avi / nd2!')
    sys.exit()
    
if not frameCtrl.loadFrameSkip(VIDEO_FILE_MODE2):
    NTH_FRAME = inputNumberMBox("Read every n-th frame: ")
    if NTH_FRAME is None:
        NTH_FRAME = 1
    else:
        NTH_FRAME = np.int(NTH_FRAME)
else:
    NTH_FRAME = None
frameCtrl.setInputVideo(VIDEO_FILE_MODE2, NTH_FRAME)

"""
    If there is more than one channel, have the user select the channel
"""
numChannels = frameCtrl.getNumChannels()
if numChannels>1:
    channels = frameCtrl.getChannels()
    channelsString = ' '.join(['['+np.str(i)+'] '+channels[i] for i in range(len(channels))])
    selectedChannel = inputNumberMBox("Select a channel: "+channelsString)
    if selectedChannel is None:
        selectedChannel = 0
    else:
        selectedChannel = int(selectedChannel)
    frameCtrl.setChannel(selectedChannel)

"""
    Set XY well
"""
if VIDEO_FILE_MODE2.endswith('avi'):
    XY_WELL = 0
else:
    XY_WELL = inputNumberMBox("XY well: ")
    if XY_WELL is None:
        frameCtrl.setXYWell(0)
    else:
        frameCtrl.setXYWell(int(XY_WELL))

"""
    Start at the last frame
"""
frameCtrl.gotoLastFrame()

totNumFrames = frameCtrl.getFrameCount()
print('Tot frame #: '+np.str(totNumFrames))

"""
    Managers and controllers
"""
circlesMgr = CircleManager()
circleDrawingMgr = SingleCircleDrawingManager()
shapeMgr = PointsManager(frameCtrl)

"""
    Get um/pixel
"""
if VIDEO_FILE_MODE2.endswith('avi'):
    umpixel = inputNumberMBox("um/pixel ratio [default: 0.66]: ")
    if umpixel is None:
        umpixel = 0.66
    else:
        umpixel = float(umpixel)
    shapeMgr.setUmPixel(umpixel)
else:
    umpixel = frameCtrl.getMicronsPerPixel()
    shapeMgr.setUmPixel(umpixel)
    
"""
    Set saving directory
"""
sourcePath = os.path.dirname(os.path.abspath(__file__))
if not (sourcePath.endswith('/') or sourcePath.endswith('\\')):
    sourcePath += '/'
#saveDir = frameCtrl.getVideoPath() + frameCtrl.getVideoBasename() + '_tracking/'
saveDir = sourcePath + 'tracking/' + frameCtrl.getVideoBasename() + '_tracking/'
shapeMgr.setTrackingDirectory(saveDir)

"""
    Load any previous shapes
"""
#loadDir = frameCtrl.getVideoPath() + frameCtrl.getVideoBasename() + '_tracking/'
loadDir = sourcePath + 'tracking/' + frameCtrl.getVideoBasename() + '_tracking/'
if os.path.exists(loadDir):
    loadAll(shapeMgr)
shapeMgr.setFrameSkip(frameCtrl.getFrameSkip())
mouseCtrl = MouseControl(circlesMgr, circleDrawingMgr, shapeMgr)

if True:
    lastFrameDrawingTime = time.time()
    
    flagReset = False          # Reset video in mode2
    flagFirstOpen = True
    isPaused = False
    flagOneFrame = False
    flagOneFrameBack = False
    flagEnableBorderWithShape = False             # Enable creating shapes with a border
    flagEnableAddingBorderToExistingShapes = False    # Enable adding border to existing shapes
    
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
    
    flagOneFrameForward = False
    flagOneFrameBack = False
    flagRefreshFrame = True
    
    """
        Frame editing:
            allows to shift / multiply all points by a factor
    """
    firstFrameEdit = 0                                    # First frame to edit (included)
    lastFrameEdit = frameCtrl.getFrameCount()-1           # Last frame to edit (included)
    xFactor = 0                                           # The factor to shift / multiply the x
                                                          # (on screen horizontal) of points by
    yFactor = 0                                           # The factor to shift / multiply the y
                                                          # (on screen vertical) of points by
    
    print('Screen factor: '+np.str(frameCtrl.getScreenFactor()))
    
    while (frameCtrl.isRunning()):
        if flagFirstOpen==True:
            cv2.namedWindow('frame')
            cv2.setMouseCallback('frame', mouseCtrl.callback)
            flagFirstOpen = False
        
        # Show frame after cuve additions
        circleIntensity = None
        if flagOneFrameForward==True or flagOneFrameBack==True or flagReset==True\
            or flagRefreshFrame or mouseCtrl.updateScreen() or shapeMgr.updateScreen():
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
                    
                # Save intensities here?
                
            if flagOneFrameBack==True:
                frameCtrl.backward()
                
                # Send new frame # to shapeMgr
                shapeMgr.setCurrentFrame(frameCtrl.getCurrentFrameNumber())
                
                flagOneFrameBack = False
            
            currentFrameNum = frameCtrl.getCurrentFrameNumber()
            if currentFrameNum==1:
                circleIntensitiesSaved = False;
            
            # Resize the frame or zoom in
            width   = frameCtrl.getFrameWidth()
            height  = frameCtrl.getFrameHeight()
            grayFrame = frameCtrl.getCurrentGrayFrame()
            
            if flagOneFrameForward==True:
                # Send new frame # to shapeMgr
                shapeMgr.setCurrentFrame(frameCtrl.getCurrentFrameNumber())
                
                if isPaused==True:
                    flagOneFrameForward = False
                else:
                    if circleIntensitiesSaved==False:
                        if False:                            
                            # Measure avg intensity for all circles
                            circlesMgr.measureAverageCircleIntensityForAllCircles(grayFrame,frameCtrl.getCurrentFrame(),frameCtrl.getCurrentFrameNumber()-1);
                            
                            # Measure avg intensity for the polygon
                            shapeMgr.measureAveragePolyIntensityForAllPolys(grayFrame,frameCtrl.getCurrentFrame(),frameCtrl.getCurrentFrameNumber()-1);

                    
            # Start our frame from the base frame
            img_ch1_draw = np.copy(frameCtrl.getCurrentFrame())
            
            # Write button information
            writeInformationText(img_ch1_draw)
            
            # Draw frame number
            if showTextFlag:
                RGB_RED = (255,0,0)
                RGB_GREEN = (0,255,0)
                RGB = TEXT_RGB
                RGB = RGB[::-1]
                RGB_RED = RGB_RED[::-1]
                RGB_GREEN = RGB_GREEN[::-1]
                filename = frameCtrl.getCurrentFilename()
                
                cv2.putText(img_ch1_draw,"Borders: ",(10,nextTextLineY+textLineHeight), font, 0.5,RGB,2)
                if flagEnableBorderWithShape:
                    cv2.putText(img_ch1_draw,"Enabled",(int(10+9*len("Add border mode: ")),nextTextLineY+textLineHeight), font, 0.5,RGB_GREEN,2)
                else:
                    cv2.putText(img_ch1_draw,"Disabled",(int(10+9*len("Add border mode: ")),nextTextLineY+textLineHeight), font, 0.5,RGB_RED,2)
                nextTextLineY += textLineHeight
                
                cv2.putText(img_ch1_draw,"Add border mode: ",(10,nextTextLineY+textLineHeight), font, 0.5,RGB,2)
                if flagEnableAddingBorderToExistingShapes:
                    cv2.putText(img_ch1_draw,"Enabled",(int(10+9*len("Add border mode: ")),nextTextLineY+textLineHeight), font, 0.5,RGB_GREEN,2)
                else:
                    cv2.putText(img_ch1_draw,"Disabled",(int(10+9*len("Add border mode: ")),nextTextLineY+textLineHeight), font, 0.5,RGB_RED,2)
                
                nextTextLineY += textLineHeight
                cv2.putText(img_ch1_draw,"File: "+filename,(10,nextTextLineY+textLineHeight), font, 0.5,RGB,2)
                nextTextLineY += textLineHeight
                cv2.putText(img_ch1_draw,"XY: "+str(int(frameCtrl.getCurrentXYWellName())+1),(10,nextTextLineY+textLineHeight), font, 0.5,RGB,2)
                nextTextLineY += textLineHeight
                cv2.putText(img_ch1_draw,"Frame: "+str(frameCtrl.getCurrentFrameNumber()),(10,nextTextLineY+textLineHeight), font, 0.5,RGB,2)
                nextTextLineY += textLineHeight
                cv2.putText(img_ch1_draw,"Z: "+str(int(frameCtrl.getZLevel())+1),(10,nextTextLineY+textLineHeight), font, 0.5,RGB,2)
                if circleIntensity is not None:
                    cv2.putText(img_ch1_draw,"Circle intenisty: "+str(circleIntensity),(10,nextTextLineY+textLineHeight*2), font, 0.5,(0,0,200),2)
                
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
                mouseCtrl.screenUpdated()
                shapeMgr.screenUpdated()
                flagRefreshFrame = False
                
        key = cv2.waitKey(100)
        
        # Remove current points
        if key&0xFF == ord('r'):
            """
            flagReset = True;
            isPaused = True
            flagOneFrameForward = False
            """
            
            # Remove last polygon
            shapeMgr.clearCurrentShape()
            flagRefreshFrame = True
            continue
        
        # Export all shapes
        if key&0xFF == ord('e'):
            saveDir = frameCtrl.getVideoPath() + frameCtrl.getVideoBasename() + '_tracking/'
            shapeMgr.exportShapesToUNet(saveDir + 'UNet/')
            continue
        
        # Space: finish shape
        if key&0xFF == 32:#ord('c'):
            if mode==3 and buttonMode==2:
                """
                polyMgr.closePoly()
                polyMgr.addPolygon(polyMgr.getCurrentPoly())
                """
                flagPolygon = shapeMgr.shapeType(shapeMgr.getCurrentShape())=='polygon'
                if flagPolygon:
                    shapeMgr.closePoly()
                shapeMgr.addShape(shapeMgr.getCurrentShape(), frameCtrl.getZSlice())
                shapeMgr.clearCurrentShape()
                mouseCtrl.setFlagEditingShape(False)
                
                """
                    Don't allow doing undos for these points
                """
                shapeMgr.blockUndoOperation(False)
                
                """
                    Update the sceen
                """
                flagRefreshFrame = True
                
                """
                    Start setting the shape border
                """
                if flagEnableBorderWithShape:
                    mouseCtrl.setFlagSettingShapeBorder(True, isAddingBorderToShape=False)
                else:
                    shapeMgr.finishShapeNoBorder()
                
                #if flagPolygon:
                #    a = shapeMgr.getPolyArea(frameCtrl.getScreenFactor())
                #    print('Poly area = ',np.round(a,3))
            continue
        
        # Quit
        if (key&0xFF == ord('q')) or (key&0xFF == ord('Q')):
            saveAll(frameCtrl, shapeMgr)
            
            """
                Exit
            """
            print('Exiting...')
            break
        
        # Finish (CTRL+f)
        if key==6:#(key&0xFF == ord('f')) or (key&0xFF == ord('F')):
            if not boolQuestionMBox("Are you sure you want to finish?"):
                continue
            
            if saveAll(frameCtrl, shapeMgr):
                """
                    Remove backup
                """
                print('Removing backup...')
                shapeMgr.removeBackup()
                print('Done!')
                
                """
                    Exit
                """
                print('Exiting...')
                break
            else:
                print("Could not save all, can't finish yet")
                continue
            
        # Save all
        if key&0xFF == ord('s'):
            saveAll(frameCtrl, shapeMgr, True)
            continue
        
        # Load from files
        if key&0xFF == ord('l'):
            print('Loading shapes...')
            loadAll(shapeMgr)
            print('Done!')
            
            # Refresh frame
            flagRefreshFrame = True
            continue
        
        # Apply tracking across frames
        if key&0xFF == ord('t'):
            print('Tracking shapes...')
            shapeMgr.trackShapes()
            print('Done!')
            # Refresh frame
            flagRefreshFrame = True
            continue
        
        """
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
        """
        
        # Set threshold
        if key&0xFF == ord('v'):
            if mode==1:
                #gThreshold = np.float(mbox("Enter the thereshold:", entry=True));
                #print('threshold=',threshold);
                pass
            if mode==2:
                #buttonMode = 1
                #mouseCtrl.setButtonMode(1)
                pass
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
            #saveAll(frameCtrl, shapeMgr)
            
            """
                Don't allow doing undos for stuff done in previous frame
            """
            shapeMgr.blockUndoOperation(True)
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
            #saveAll(frameCtrl, shapeMgr)
            
            """
                Don't allow doing undos for stuff done in previous frame
            """
            shapeMgr.blockUndoOperation(True)
            continue
            
        # Up arrow
        if int(key) == 2490368:
            frameCtrl.increaseZSlice()  
            flagRefreshFrame = True                        
            continue
            
        # Down arrow
        if int(key) == 2621440:
            frameCtrl.decreaseZSlice()
            flagRefreshFrame = True
            continue
            
        if key&0xFF == ord('-'):
            if mode==1:
                pass
            continue
        
        if key&0xFF == 9:
            showTextFlag = not showTextFlag
            flagRefreshFrame = True
            continue
        
        # 'u' key
        if key&0xff == ord('u'):
            #print('u key pressed!')
            shapeMgr.undoLastRemoval()
            continue
        
        # 'a' key
        if key&0xff == ord('a'):
            flagEnableAddingBorderToExistingShapes = not flagEnableAddingBorderToExistingShapes
            flagRefreshFrame = True
            mouseCtrl.setFlagEnableAddingBorder(flagEnableAddingBorderToExistingShapes)
            continue
        
        # 'b' key
        if key&0xff == ord('b'):
            flagEnableBorderWithShape = not flagEnableBorderWithShape
            flagRefreshFrame = True
            mouseCtrl.setFlagEnableBorderWithShape(flagEnableBorderWithShape)
            continue
        
        # '1' key
        if False and key==49:
            """
                Display a message box:
                    Set the first frame to edit (inc.):
            """
            firstFrameEdit = int(inputNumberMBox("Set the first frame to edit (inc.): "))
            continue
        
        # '2' key
        if False and key==50:
            """
                Display a message box:
                    Set the last frame to edit (inc.):
            """
            lastFrameEdit = int(inputNumberMBox("Set the last frame to edit (inc.): "))
            continue
        
        # CTRL+x key
        if False and key==24:
            """
                Display a message box:
                    Shift/Multiply in x by:
            """
            xFactor = inputNumberMBox("Shift/multiply in x by: ")
            continue
        
        # CTRL+y key
        if False and key==25:
            """
                Display a message box:
                    Shift/Multiply in y by:
            """
            yFactor = inputNumberMBox("Shift/multiply in y by: ")
            continue
        
        # ENTER
        if False and key==13:
            """
               Display a message box:
                   Editing
                   From frame ... to frame ... (inc)
                   x factor: ..., y factor: ... 
            """
            if xFactor is not None and yFactor is not None and firstFrameEdit is not None and lastFrameEdit is not None:
                ret = twoOptionQuestionMBox('Editing'+'\n'+'From frame '+np.str(firstFrameEdit)+' to frame '+np.str(lastFrameEdit)+' (inc.)'+'\n'+'x factor: '+np.str(xFactor)+' y factor: '+np.str(yFactor),'Shift','Multiply')
                if ret==True:
                    shapeMgr.editPointsShift(firstFrameEdit, lastFrameEdit, yFactor, xFactor)
                elif ret==False:
                    shapeMgr.editPointsMultiply(firstFrameEdit, lastFrameEdit, yFactor, xFactor)
                flagRefreshFrame = True
            continue
        
        # CTRL+ENTER
        if False and key==10:
            """
                Finalize editing the points
            """
            if boolQuestionMBox('Finalize most recent edit?'):
                shapeMgr.finalizeMostRecentEdit()
                saveAll(frameCtrl, shapeMgr)
            continue
        
        # Goto frame
        if key&0xFF == ord('g'):
            gotoFrameNum = int(inputNumberMBox("Go to frame: "))
            
            if frameCtrl.setCurrentFrame(gotoFrameNum):
                shapeMgr.setCurrentFrame(gotoFrameNum)
                flagRefreshFrame = True
            continue
            
        """
            Detect window closing with 'X'
        """
        if not (cv2.getWindowProperty('frame', 0) >= 0):
            break
         
        # Save last button press time
        prevTime = time.time()

"""
    Save all progress
"""
#saveAll(frameCtrl, shapeMgr)

"""
    Free resources
"""
frameCtrl.release()
cv2.destroyAllWindows()