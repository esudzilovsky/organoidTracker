# -*- coding: utf-8 -*-
"""
Created on Fri Apr 20 13:05:59 2018

@author: Edward
"""
from __future__ import print_function

from nd2reader import ND2Reader
import numpy as np
import ctypes
from autoBrightnessContrast import AutoBrightnessContrast
import ntpath
import cv2
from skimage import color
from PIL import Image
import os
from natsort import natsorted
from time import time

"""
    This class handles getting the frames to display
"""
class FrameControlND2:
    def __init__(self):
        
        """
            Figure out screen dimensions to adapt the video size to be displayed
        """
        self.__findScreenSize()
        """
            This class is a tool to auto adjust grayscale image brightness and contrast
            (should expand to RGB for faster processing, right now I manually convert to
            RGB after using this on the image)
        """
        self.autoBrightnessContrast = AutoBrightnessContrast()
        
        self.frame = None              # RGB numpy array containing 0-255 values for intensity
        self.grayFrame = None          # 2D numpy array containing 0-255 values for intensity
        
        self.screenFactor = None       # The factor the image height/width is multiplied by before display
        self.readEveryNthFrame = 1     # Read every 1st or 2nd or 3rd etc frame
        self.nd2Filename = None        # *.nd2 file path + name
        self.nd2Reader = None          # *.nd2 file reader
        #self.XYWellNum = None          # XY well # to read
        self.zSlice = 0                # The index of the z slice used (this is NOT the slice # directly)
        self.zLevels = None            # Total number of z slices
        self.channels = None           # A list of strings corresponding to video channels
        self.readChannelIndex = None   # The index of the channel, from self.channels that we read from
        self.wantedWidth = None        # The width we desire to make the image file to view on screen
        self.wantedHeight = None       # The hight we desire to make the image file to view on screen
        self.originalWidth = None      # The original image file width as stored
        self.originalHeight = None     # The original image file height as stored
        self.fieldsOfView = None       # A list of XY well names (as in *.nd2 file)
        #self.totNumFrames = None       # Total number of frames in current file
        #self.currentFrameNum = 0       # Frame number in current file, starting with 0
        
        """
            Going over multiple files
        """
        self.nd2Folder = None                           # The folder containing all *.nd2 files
        self.nd2Filenames = None                        # All (full) *.nd2 filenames in folder
        #self.currentFileIndex = 0                      # Index of current file in self.nd2Filenames
        self.totNumFramesAllFiles = 0                   # Total number of frames for all files
        self.currentFrameNumAllFiles = 0                # Current frame number, across all files
        self.nd2Readers = None                          # Contains the readers for all *.nd2 files
        self.currentFrameNumAllFilesAdjusted = None     # Current effctive frame (adjusted for skipping frames)
        self.totNumFramesAdjustedAllFiles = None        # Tot # of effctives frames (adjusted for skipping frames)
        """
            We want to map from:
                frame # -> (*.nd2 file index, *.nd2 file frame #)
        """
        self.frameNum2Nd2File = None
    
    def getFrameWidth(self):
        return self.originalWidth
    
    def getFrameHeight(self):
        return self.originalHeight
        
    """
        Release resources
    """
    def release(self):
        self.__release()
        
    def isRunning(self):
        return True#self.cap.isOpened()
        
    """
        Brooke wants the names to start with 1 and not 0 so subtract 1
    """
    def setXYWell(self, XYWellName):
        #print('XY array: ',self.fieldsOfView)
        #print('XY name: ',XYWellName)
        XYWellName = int(XYWellName)-1
        self.currentXYWellNumber = np.where(self.fieldsOfView==int(XYWellName))[0][0]
        #print('Result:')
        #print('   self.currentXYWellNumber: ',self.currentXYWellNumber)
        #print('   well name: ',self.fieldsOfView[self.currentXYWellNumber])
        
    """
        Moves to the last frame, but doesn't update the screen frame
    """
    def gotoLastFrame(self):
        self.currentFrameNumAllFiles = int(int((self.totNumFramesAllFiles-1)/self.readEveryNthFrame)*self.readEveryNthFrame)
        
    """
        Moves to the first frame, but doesn't update the screen frame
    """
    def gotoFirstFrame(self):
        self.currentFrameNumAllFiles = 0
        
    def gotoFrame(self, frameNum):
        self.currentFrameNumAllFiles = int(frameNum)
        
    def getFrameSkipPathnames(self, nd2Filename):
        if os.path.isdir(nd2Filename):
            return nd2Filename+'/'+'frameSkip'
        else:
            return nd2Filename + '_frameSkip'
    """
        Load file skip
    """
    def loadFrameSkip(self, nd2Filename):
        frameSkipFName = self.getFrameSkipPathnames(nd2Filename)+'.npy'
        if os.path.exists(frameSkipFName):
            self.readEveryNthFrame = np.load(frameSkipFName).item()
            return True
        return False
    
    def saveFrameSkip(self, nd2Filename):
        frameSkipFName = self.getFrameSkipPathnames(nd2Filename)
        np.save(frameSkipFName, self.readEveryNthFrame)
    
    def setInputVideo(self, nd2Filename, readEveryNthFrame):
        if os.path.isdir(nd2Filename):
            self.nd2Folder = os.path.realpath(nd2Filename)
            self.nd2Filenames = []
            
            """
                Get all files in folder
            """
            for root, dirs, filenames in os.walk(self.nd2Folder):
                # Only root directory
                if os.path.realpath(root)==self.nd2Folder:
                    for f in filenames:
                        if f.endswith('.nd2'):
                            self.nd2Filenames.append(root +'/' + f)
            
            """
                Windows sort
            """
            self.nd2Filenames = natsorted(self.nd2Filenames)
            
            """
                SIMULATION
                If we only have one file make it 3 of the same file
                to simulate a multi-file app.
            """
            #if True:
            #    self.nd2Filenames.append(self.nd2Filenames[0])
            #    self.nd2Filenames.append(self.nd2Filenames[0])
            
            """
                We want to map from:
                    frame # -> (*.nd2 file index, *.nd2 file frame #)
            """
            self.frameNum2Nd2File = dict()
            self.nd2Readers = []
            frameNum = 0
            nd2FileIndex = 0
            print('Creating ND2 file frame mapping...')
            for f in self.nd2Filenames:
                print('   file = ',f)
                nd2Reader = ND2Reader(f)
                self.nd2Readers.append(nd2Reader)
                nd2FileNumFrames = int(nd2Reader.metadata['num_frames'])
                print('   has '+np.str(nd2FileNumFrames)+' frames.')
                
                for frameInFile in range(nd2FileNumFrames):
                    self.frameNum2Nd2File[frameNum] = (nd2FileIndex, frameInFile)
                    frameNum += 1
                    
                nd2FileIndex += 1
            print('Done!')
            self.totNumFramesAllFiles = frameNum # Total # of frames
            
            """
                Set current file
            """
            #self.currentFileIndex = 0
            self.nd2Filename = self.nd2Filenames[-1]
            self.nd2Reader = self.nd2Readers[-1]
            pass
        else:
            """
                Set current file
            """
            #self.currentFileIndex = 0
            self.nd2Filename = nd2Filename
            """
                Read first file
            """
            nd2Reader = ND2Reader(self.nd2Filename)
            self.nd2Readers = []
            self.nd2Readers.append(nd2Reader)
            self.nd2Reader = nd2Reader
            
            self.nd2Filenames = [nd2Filename]
            self.nd2Folder = os.path.dirname(nd2Filename)
            self.totNumFramesAllFiles = int(self.nd2Reader.metadata['num_frames'])
            
            """
                Create mapping
            """
            print('Creating ND2 file frame mapping...')
            self.frameNum2Nd2File = dict()
            frameNum = 0
            nd2FileIndex = 0
            for f in self.nd2Filenames:
                nd2Reader = ND2Reader(f)
                self.nd2Readers.append(nd2Reader)
                nd2FileNumFrames = int(nd2Reader.metadata['num_frames'])
                
                for frameInFile in range(nd2FileNumFrames):
                    self.frameNum2Nd2File[frameNum] = (nd2FileIndex, frameInFile)
                    frameNum += 1
                    
                nd2FileIndex += 1
            print('Done!')
        
        self.micronsPerPixel = self.nd2Reader.metadata['pixel_microns']
        self.currentFrameNumAllFiles = int(self.totNumFramesAllFiles-1)
        if readEveryNthFrame is not None:
            self.readEveryNthFrame = int(readEveryNthFrame)
        self.totNumFramesAdjustedAllFiles = int(np.floor(float(self.totNumFramesAllFiles)/float(self.readEveryNthFrame)))
        self.currentFrameNumAllFilesAdjusted = int(self.totNumFramesAdjustedAllFiles-1)
        #self.currentFrameNum = 0
        
        #print('self.nd2Reader.metadata: ',self.nd2Reader.metadata)
        
        #self.totNumFrames = int(self.nd2Reader.metadata['num_frames'])
        self.zLevels = self.nd2Reader.metadata['z_levels']
        
        """
            Select middle z channel
        """
        self.zSlice = int(np.floor(len(self.zLevels)/2)+1)-1
        
        self.channels = self.nd2Reader.metadata['channels']
        self.fieldsOfView = np.array(self.nd2Reader.metadata['fields_of_view'],dtype=int)
        self.XYWellCount = len(self.fieldsOfView)
        print('XY wells count: '+np.str(self.XYWellCount))
        self.currentXYWellNumber = int(0)
        self.readChannelIndex = int(0)

        width = self.nd2Reader.metadata['width']   # float
        height = self.nd2Reader.metadata['height'] # float
        self.originalWidth = np.copy(width)
        self.originalHeight = np.copy(height)
        
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
                
        self.wantedWidth = float(self.screenWidth-75)
        self.wantedHeight = float(self.screenHeight-75)
        
        #self.__readImageFromND2()
        #self.__newFrame()
        
    def getMicronsPerPixel(self):
        return self.micronsPerPixel
        
    def getCurrentFilename(self):
        path, filename = os.path.split(self.nd2Filenames[self.frameNum2Nd2File[self.currentFrameNumAllFiles][0]])
        return filename
                
    def getFrameSkip(self):
        return int(self.readEveryNthFrame)
    
    def increaseZSlice(self):
        #print('increaseZSlice')
        self.zSlice += 1
        # Careful not to overflow
        if len(self.zLevels)<=np.abs(self.zSlice):
            #print('reset slice')
            self.zSlice -= 1
        else:
            #print('load new image')
            self.__readImageFromND2()
            self.__newFrame()
    
    def decreaseZSlice(self):
        #print('decreaseZSlice')
        self.zSlice -= 1
        # Careful not to overflow
        if len(self.zLevels)<=np.abs(self.zSlice) or self.zSlice<0:
            #print('reset slice')
            self.zSlice += 1
        else:
            #print('load new image')
            self.__readImageFromND2()
            self.__newFrame()
            
    def getZSlice(self):
        return self.zSlice
    
    def getZLevel(self):
        return self.zLevels[self.zSlice]
                
    def getScreenFactor(self):
        return self.screenFactor
    
    """
        Reset video to first frame
    """
    """
    def resetVideo(self):
        self.currentFrameNumAllFiles = 0
        
        self.__readImageFromND2()
        
        # New frame
        self.__newFrame()
    """
        
    """
        Returns current frame #, starting from 0
    """
    def getCurrentFrameNumber(self):
        return self.currentFrameNumAllFiles
    
    def getCurrentXYWellNumber(self):
        return self.currentXYWellNumber
    
    """
        Returns the XY well name as set in the *.nd2 file
    """
    def getCurrentXYWellName(self):
        return self.fieldsOfView[self.currentXYWellNumber]
    
    """
        Returns the current frame number, adjusted for the number of frames read every time.
        This starts from 0.
    """
    def getCurrentFrameNumberAdjusted(self):
        return int(self.currentFrameNumAllFilesAdjusted)#np.int((self.currentFrameNumAllFiles) / self.readEveryNthFrame)
    
    """
        Returns video filename, no path included
    """
    def getVideoBasename(self):
        return ntpath.basename(self.nd2Filename)
    
    """
        Returns number of channels
    """
    def getNumChannels(self):
        return len(self.channels)
    
    """
        Returns video channels
    """
    def getChannels(self):
        return self.channels
    
    """
        Sets the video channel used
    """
    def setChannel(self, channelNum):
        if channelNum>=len(self.channels):
            self.readChannelIndex = 0
        else:
            self.readChannelIndex = channelNum
    
    """
        Returns video filename path
    """
    def getVideoPath(self):
        return ntpath.dirname(self.nd2Filename)+"/"
    
    """
        Returns the current frame, which is resized to fit the screen
    """
    def getCurrentFrame(self):
        if self.frame is None:
            self.__readImageFromND2()
            self.__newFrame()
        return self.frame
    
    """
        Returns the total # of frames
    """
    def getFrameCount(self):
        return self.totNumFramesAllFiles
    
    def addFakeFramesToBeginning(self, numFakeFrames):
        self.frameNum2Nd2File = dict()
        self.nd2Readers = []
        
        nd2FileIndex = 0
        frameInFile = 0
        for frameNum in range(numFakeFrames):
            self.frameNum2Nd2File[frameNum] = (nd2FileIndex, frameInFile)
        
        frameNum = numFakeFrames
        nd2FileIndex = 0
        for f in self.nd2Filenames:
            nd2Reader = ND2Reader(f)
            self.nd2Readers.append(nd2Reader)
            nd2FileNumFrames = int(nd2Reader.metadata['num_frames'])
            
            for frameInFile in range(nd2FileNumFrames):
                self.frameNum2Nd2File[frameNum] = (nd2FileIndex, frameInFile)
                frameNum += 1
                
            nd2FileIndex += 1
        self.totNumFramesAllFiles = frameNum
    
    """
        Returns total number of XY wells
    """
    def getXYWellCount(self):
        return self.XYWellCount
    
    def __getWantedImageSize(self):
        return (self.wantedWidth, self.wantedHeight)
    
    def __getOriginalImageSize(self):
        return (self.originalWidth, self.originalHeight)
    
    """
        Reads the image according to:
            - self.currentFrameNum
            - self.XYWellNum
            - self.zSlice
            - Wanted image size
    """
    def __readImageFromND2(self):
        width, height = self.__getOriginalImageSize()
        
        if self.currentFrameNumAllFiles not in self.frameNum2Nd2File:
            print('__readImageFromND2 error: current frame index not in *.nd2 frame map!')
            return
        nd2FileIndex, nd2FrameIndex = self.frameNum2Nd2File[self.currentFrameNumAllFiles]
        
        #print('self.XYWellNum: ',self.XYWellNum)
        nd2Reader = self.nd2Readers[nd2FileIndex]
        imageArray = nd2Reader.parser.get_image_by_attributes(\
                                               int(nd2FrameIndex),\
                                               int(self.fieldsOfView[self.currentXYWellNumber]),\
                                               self.channels[self.readChannelIndex],
                                               self.zLevels[self.zSlice],\
                                               int(height),\
                                               int(width))
        
        """
        imageArray = self.nd2Reader.parser.get_image_by_attributes(0, 0,\
                                               u'BF', 0,\
                                               2044, 2048)
        """
        self.frame = np.array(np.array(imageArray,dtype=float)/np.iinfo(np.uint16).max*255, dtype=np.uint8)
    
    def getFrame(self, xy, t):
        width, height = self.__getOriginalImageSize()
        
        nd2FileIndex, nd2FrameIndex = self.frameNum2Nd2File[t]
        
        #print('self.XYWellNum: ',self.XYWellNum)
        nd2Reader = self.nd2Readers[nd2FileIndex]
        imageArray = nd2Reader.parser.get_image_by_attributes(\
                                               int(nd2FrameIndex),\
                                               int(self.fieldsOfView[xy]),\
                                               self.channels[self.readChannelIndex],
                                               self.zLevels[self.zSlice],\
                                               int(height),\
                                               int(width))
        
        """
        imageArray = self.nd2Reader.parser.get_image_by_attributes(0, 0,\
                                               u'BF', 0,\
                                               2044, 2048)
        """
        frame = np.array(np.array(imageArray,dtype=float)/np.iinfo(np.uint16).max*255, dtype=np.uint8)
    
        return self.__adjustBrightnessAndConstrast(frame)
    """
        Set to a specific frame
    """
    def setCurrentFrame(self, frameNum):
        frameNum = int(frameNum)
        
        if frameNum<0 or frameNum>=self.totNumFramesAllFiles or frameNum%self.readEveryNthFrame!=0:
            print('   Error: invalid frame number!')
            print('   Frame # must be >=0 and <='+np.str(self.totNumFramesAllFiles)+' and divisible by '+np.str(self.readEveryNthFrame))
            return False
        
        #self.currentFrameNumAllFiles += self.readEveryNthFrame
        #self.currentFrameNumAllFilesAdjusted += 1
        self.currentFrameNumAllFiles = frameNum
        self.currentFrameNumAllFilesAdjusted = int(frameNum/self.readEveryNthFrame)
        
        self.__readImageFromND2()
        
        # New frame
        self.__newFrame()
        
        return True
    
    """
        Moves one frame forward
    """
    def forward(self):
        if self.totNumFramesAllFiles<=self.currentFrameNumAllFiles+self.readEveryNthFrame:
            return
        
        self.currentFrameNumAllFiles += self.readEveryNthFrame
        self.currentFrameNumAllFilesAdjusted += 1
        #print('self.readEveryNthFrame: ',self.readEveryNthFrame)
        #print('self.currentFrameNum: ',self.currentFrameNum)
                
        self.__readImageFromND2()
        
        # New frame
        self.__newFrame()
    
    """
        Moves one frame backward
    """
    def backward(self, nframes=None):
        if self.currentFrameNumAllFiles-self.readEveryNthFrame<0:
            return
        self.currentFrameNumAllFiles -= self.readEveryNthFrame
        self.currentFrameNumAllFilesAdjusted -= 1
        
        self.__readImageFromND2()
        
        # New frame
        self.__newFrame()
        
    """
    def backwardEOF(self):
        self.__findFrameNum()
        self.cap.set(1,self.currentFrameNum-1)
        ret1, self.frame = self.cap.read()
        
        # New frame
        #self.__newFrame()
    """
    
    """
    def __findFrameNum(self):
        self.currentFrameNum = int(self.cap.get(1))
    """
    
    """
        Returns current frame, in grayscale
    """
    def getCurrentGrayFrame(self):
        if self.grayFrame is None:
            self.__readImageFromND2()
            self.__newFrame()
        return self.grayFrame
    
    """
        Called after the frame changes
    """
    def __newFrame(self):
        if self.frame is not None:
            self.frame = self.__resizeImage(self.frame)
            self.grayFrame = color.rgb2gray(self.frame)#cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            self.grayFrame = self.__adjustBrightnessAndConstrast(self.grayFrame)
            self.frame = color.gray2rgb(self.grayFrame)#cv2.cvtColor(self.grayFrame, cv2.COLOR_GRAY2RGB)
        #self.__findFrameNum()
    
    """
        Resizes the image to fit the screen
    """
    def __resizeImage(self, image):
        width   = image.shape[0]
        height  = image.shape[1]
        
        self.frameWidth = int(width*self.screenFactor)
        self.frameHeight = int(height*self.screenFactor)
        
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
        pass
            
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
        
if __name__=='__main__':
    frameCtrl = FrameControlND2()
    if False:
        frameCtrl.setInputVideo('C:/ND2/20180315uc4007.nd2', 0, 1)
        frameCtrl.getCurrentFrame()
        
    if True:
        frameCtrl.setInputVideo('C:/ND2/20180315uc4006_crop.nd2', 0, 1)
        frameCtrl.getCurrentFrame()
        frameCtrl.forward()
        frameCtrl.forward()
        frameCtrl.forward()
        #frameCtrl.forward()
        #frameCtrl.forward()