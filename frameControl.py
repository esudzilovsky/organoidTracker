# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 16:35:47 2018

@author: Edward
"""

from __future__ import print_function

import cv2
import os
import numpy as np
import ctypes
from autoBrightnessContrast import AutoBrightnessContrast
import ntpath

"""
    This class handles getting the frames to display
"""
class FrameControl:
    def __init__(self):#, screenWidth, screenHeight):
        #self.screenHeight = screenHeight
        #self.screenWidth = screenWidth
        self.__findScreenSize()
        self.cap = None
        self.frame = None
        self.currentFrameNum = 0
        self.autoBrightnessContrast = AutoBrightnessContrast()
        self.screenFactor = None
        self.readEveryNthFrame = 1
        self.currentFrameNumAllFilesAdjusted = None
        self.grayFrame = None
        self.frameWidth = None
        self.frameHeight = None
        
    """
        Release resources
    """
    def release(self):
        self.__release()
        
    def isRunning(self):
        return self.cap.isOpened()
    
    def getFrameSkipPathnames(self, videoFilename):
        if os.path.isdir(videoFilename):
            return videoFilename+'/'+'frameSkip'
        else:
            return videoFilename + '_frameSkip'
        
    def getNumChannels(self):
        return 1
    
    def getFrameWidth(self):
        print('frameControl (not ND2), self.frameWidth = ',self.frameWidth)
        return self.frameWidth
    
    def getFrameHeight(self):
        return self.frameHeight
    
    def setXYWell(self, x):
        pass
    
    """
        Load file skip
    """
    def loadFrameSkip(self, videoFilename):
        frameSkipFName = self.getFrameSkipPathnames(videoFilename)+'.npy'
        if os.path.exists(frameSkipFName):
            self.readEveryNthFrame = np.load(frameSkipFName).item()
            return True
        return False
    
    def saveFrameSkip(self, videoFilename):
        frameSkipFName = self.getFrameSkipPathnames(videoFilename)
        np.save(frameSkipFName, self.readEveryNthFrame)
        
    def setInputVideo(self, videoFilename, readEveryNthFrame):
        if readEveryNthFrame is not None:
            self.readEveryNthFrame = readEveryNthFrame
        self.videoFilename = videoFilename
        self.cap = cv2.VideoCapture(videoFilename)
        self.totNumFrames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.totNumFramesAdjustedAllFiles = int(np.floor(float(self.totNumFrames)/float(self.readEveryNthFrame)))
        #print('self.totNumFramesAdjustedAllFiles: ',self.totNumFramesAdjustedAllFiles)
        self.currentFrameNumAllFilesAdjusted = int(self.totNumFramesAdjustedAllFiles-1)
        #print('self.currentFrameNumAllFilesAdjusted: ',self.currentFrameNumAllFilesAdjusted)

        width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)   # float
        height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) # float
        self.frameWidth = width
        self.frameHeight = height
        
        factorWidth = float(self.screenWidth-75)/float(width)
        factorHeight = float(self.screenHeight-75)/float(height)
        
        if factorHeight<1 and factorWidth<1:
            if np.abs(factorHeight-1)>np.abs(factorWidth-1):
                self.screenFactor = factorHeight
            else:
                self.screenFactor = factorWidth
        elif factorHeight<1:
            self.screenFactor = factorHeight
        elif factorWidth<1:
            self.screenFactor = factorWidth
        else:
            if np.abs(factorHeight-1)<np.abs(factorWidth-1):
                self.screenFactor = factorHeight
            else:
                self.screenFactor = factorWidth
                
        #self.__setFrame(self.totNumFrames)
        
    def getScreenFactor(self):
        return self.screenFactor
    
    """
        Reset video to first frame
    """
    def resetVideo(self):
        self.cap.release()
        self.cap = cv2.VideoCapture(self.videoFilename)
        ret, self.frame = self.cap.read()
        
        # New frame
        self.__newFrame()
        
    """
        Returns current frame #, starting from 0
    """
    def getCurrentFrameNumber(self):
        return self.currentFrameNum
    
    """
        Returns the current frame number, adjusted for the number of frames read every time.
        This starts from 0.
    """
    def getCurrentFrameNumberAdjusted(self):
        #print('getCurrentFrameNumberAdjusted :' ,self.currentFrameNumAllFilesAdjusted)
        return int(self.currentFrameNumAllFilesAdjusted)
    
    """
        Returns video filename, no path included
    """
    def getVideoBasename(self):
        return ntpath.basename(self.videoFilename)
    
    """
        Returns video filename path
    """
    def getVideoPath(self):
        return ntpath.dirname(self.videoFilename)+"/"
    
    """
        Returns the current frame, which is resized to fit the screen
    """
    def getCurrentFrame(self):
        return self.frame
    
    """
        Returns the total # of frames
    """
    def getFrameCount(self):
        return int(self.totNumFrames)
    
    def addFakeFramesToBeginning(self):
        pass
    
    def getXYWellCount(self):
        return int(1)
    
    def getFrameSkip(self):
        return int(self.readEveryNthFrame)
    
    def getFrameWidth(self):
        pass
    
    def getFrameHeight(self):
        pass
    
    def increaseZSlice(self):
        pass
    
    def decreaseZSlice(self):
        pass
    
    def getZSlice(self):
        return 0
    
    def getZLevel(self):
        return 1
    
    def getCurrentXYWellNumber(self):
        return int(0)
    
    def getCurrentXYWellName(self):
        return int(1)
    
    def getCurrentFilename(self):
        path, filename = os.path.split(self.videoFilename)
        return filename
    
    """
        Goes to last frame
    """
    def gotoLastFrame(self):
        #while self.forward():
        #    pass
        self.__setFrame(self.totNumFrames-1)
        ret, self.frame = self.cap.read()
        self.__newFrame()
        
    """
        Sets the current frame
    """
    def setCurrentFrame(self, frameNum):
        frameNum = int(frameNum)
        
        if frameNum<0 or frameNum>=self.totNumFrames or frameNum%self.readEveryNthFrame!=0:
            print('   Error: invalid frame number!')
            print('   Frame # must be >=0 and <='+np.str(self.totNumFramesAllFiles)+' and divisible by '+np.str(self.readEveryNthFrame))
            return False
        
        self.currentFrameNumAllFilesAdjusted = frameNum/self.readEveryNthFrame
        
        """
            Are we moving forwards or backwards?
        """
        if self.currentFrameNum<frameNum:
            """
                Move forward
            """
            count = frameNum-self.currentFrameNum
            while count>0:
                ret, self.frame = self.cap.read()
                if self.frame is None:
                    self.backwardEOF()
                    
                    self.__newFrame()
                    return False
                count -= 1
            
            # New frame
            self.__newFrame()
            return True
        elif self.currentFrameNum>frameNum:
            """
                Move backward
            """
            
            count = self.currentFrameNum-frameNum
            while count>0:
                self.__findFrameNum()
                self.cap.set(1,self.currentFrameNum-1)
                ret1, self.frame = self.cap.read()
                count -= 1
            
            # New frame
            self.__newFrame()
            
            return True
    
    """
        Moves one frame forward
    """
    def forward(self):
        if self.totNumFrames<=self.getCurrentFrameNumber()+self.readEveryNthFrame:
            return
        #print('forward')
        self.currentFrameNumAllFilesAdjusted += 1
        
        count = self.readEveryNthFrame
        while count>0:
            ret, self.frame = self.cap.read()
            if self.frame is None:
                self.backwardEOF()
                
                self.__newFrame()
                return False
            count -= 1
        
        # New frame
        self.__newFrame()
        return True
    
    """
        Moves one frame backward
    """
    def backward(self, nframes=None):
        if nframes is None:
            nframes = self.readEveryNthFrame
        #self.currentFrameNum = int(self.cap.get(1))
        
        if self.getCurrentFrameNumber()-self.readEveryNthFrame<0:
            return
        self.currentFrameNumAllFilesAdjusted -= 1
        
        count = nframes
        while count>0:
            self.__findFrameNum()
            self.cap.set(1,self.currentFrameNum-1)
            ret1, self.frame = self.cap.read()
            count -= 1
        
        # New frame
        self.__newFrame()
        
    def __setFrame(self, frameNum):
        self.cap.set(1,frameNum)
        self.__newFrame()
        
    def backwardEOF(self):
        self.__findFrameNum()
        self.cap.set(1,self.currentFrameNum-1)
        ret1, self.frame = self.cap.read()
        
        # New frame
        #self.__newFrame()
        
    def __findFrameNum(self):
        self.currentFrameNum = int(self.cap.get(1))-1
    
    """
        Returns current frame, in grayscale
    """
    def getCurrentGrayFrame(self):
        return self.grayFrame
    
    """
        Called after the frame changes
    """
    def __newFrame(self):
        if self.frame is not None:
            self.frame = self.__resizeImage(self.frame)
            self.grayFrame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            self.grayFrame = self.__adjustBrightnessAndConstrast(self.grayFrame)
            self.frame = cv2.cvtColor(self.grayFrame, cv2.COLOR_GRAY2RGB)
        self.__findFrameNum()
    
    """
        Resizes the image to fit the screen
    """
    def __resizeImage(self, image):
        width   = image.shape[0]
        height  = image.shape[1]
        
        """
        #print('width: ',width)
        #print('height: ',height)
        
        #print('self.screenWidth: ',self.screenWidth)
        #print('self.screenHeight: ',self.screenHeight)
        
        factorWidth = float(self.screenWidth-75)/float(width)
        factorHeight = float(self.screenHeight-75)/float(height)
        
        #print('factorWidth: ',factorWidth)
        #print('factorHeight: ',factorHeight)
        
        if factorHeight<1 and factorWidth<1:
            if np.abs(factorHeight-1)>np.abs(factorWidth-1):
                factor = factorHeight
            else:
                factor = factorWidth
        elif factorHeight<1:
            factor = factorHeight
        elif factorWidth<1:
            factor = factorWidth
        else:
            if np.abs(factorHeight-1)<np.abs(factorWidth-1):
                factor = factorHeight
            else:
                factor = factorWidth
        
        """
        self.frameWidth = int(width*self.screenFactor)
        self.frameHeight = int(height*self.screenFactor)
        
        #print('self.frameWidth: ',self.frameWidth)
        #print('self.frameHeight: ',self.frameHeight)
        #print('factor: ',factor)
        return cv2.resize(image, (self.frameHeight, self.frameWidth), interpolation=cv2.INTER_CUBIC)
    
    """
        Returns screen size
    """
    def __findScreenSize(self):
        user32 = ctypes.windll.user32
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        self.screenHeight = screensize[1]
        self.screenWidth = screensize[0]
        
    """
        Release resources
    """
    def __release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            
    """
    """
    def __adjustBrightnessAndConstrast(self, im):
        #cv2.imwrite('imagePre.png',im)
        im = self.autoBrightnessContrast.autoAdjust(im)
        #cv2.imwrite('imagePost.png',im)
        return im
        
        """
        #return cv2.equalizeHist(im)
        # create a CLAHE object (Arguments are optional).
        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8,8))
        return clahe.apply(im)
        """