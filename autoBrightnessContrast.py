# -*- coding: utf-8 -*-
"""
Created on Tue Apr 17 13:53:05 2018

@author: Edward
"""

from __future__ import print_function

import cv2
import numpy as np
import sys

"""
    This class auto adjusts the brightness and contrast of
    GRAYSCALE images.
    
    It finds the range of 'interesting' pixel
    intensity values in the image [imin, imax] then maps linearly
    (evenly split) from those to [0,255]. Pixel values [0,min]
    are mapped to 0, and values [max,255] are mapped to 255
    (saturated).
"""
class AutoBrightnessContrast:
    def __init__(self):
        self.AUTO_THRESHOLD = 5000
    
    """
        Automatically adjusts brightness and contrast
        image - must be grayscale!
    """
    def autoAdjust(self, image):
        if len(image.shape)>2:
            print('autoAdjust() -- Error!, we can only auto adjust grayscale images right now!\nLook at how ImageJ code does this for color images!')
            print('In ImageJ Java code this is located at ContrastAdjuster.java | autoAdjust()')
            return None
        
        pixelCount = self.getPixelCount(image)
        limit = pixelCount/10
        
        """
            Histogram
        """
        histogram = cv2.calcHist([image],[0],None,[256],[0,256])
        histogram = np.ndarray.flatten(histogram)
        histMin = 0#np.argmax(histogram>0)
        histMax = 255#histogram.shape[0]-np.argmax(histogram[::-1]>0)
        nBins = 256
        
        statsMin = 0
        statsMax = 256
        if statsMin<histMin:
            statsMin = histMin #!!!
        if statsMax>histMax:
            statsMax = histMax #!!!
        
        binSize = float(histMax-histMin)/float(nBins)
        
        """
            Threshold
        """
        autoThreshold = self.AUTO_THRESHOLD
        threshold = pixelCount/autoThreshold
        
        i = -1
        found = False
        count = None
        while True:
            i += 1
            count = histogram[i];
            if count>limit:
                count = 0;
            found = count > threshold
                
            if not (not found and i<255):
                break
        
        hmin = np.copy(i)
        i = 256
        
        while True:
            i -= 1
            count = histogram[i]
            if count>limit:
                count = 0
            found = count > threshold
            
            if not (not found and i>0):
                break
            
        hmax = np.copy(i)
        #roi = self.getROI(image)
        
        if hmax>=hmin:
            #if RGBImage:
            #
            fmin = histMin+hmin*binSize
            fmax = histMin+hmax*binSize
            if fmin==fmax:
                fmin = statsMin
                fmax = statsMax
            image = self.setMinAndMax(image, histogram, fmin, fmax)
        else:
            #self.reset(image, ?)
            print('autoAdjust() -- Error: this part of the code has not been completed yet...')
            return None
        #self.updateScrollBars(None, False)
        return image
    
    def getPixelCount(self, image):
        return image.shape[0] * image.shape[1]
    
    def getROI(self, image):
        pass
    
    def setMinAndMax(self, image, histogram, fmin, fmax):
        #print('fmin = '+np.str(fmin)+' fmax = '+np.str(fmax))
        
        # linearly map from [fmin,fmax] to [0,255]
        imin, imax = int(fmin), int(fmax)
        cdf = np.zeros_like(histogram, dtype=np.uint8)
        cdf[imax:] = 255
        cdf[imin:imax] = np.array(np.linspace(0,255,imax-imin),dtype=int)
        
        image = cdf[image]
        
        return image