# -*- coding: utf-8 -*-
"""
Created on Thu Jul 26 15:13:51 2018

@author: Edward
"""
from __future__ import print_function

import numpy as np
from expandCircle import fitCircle
from expandEllipse import fitEllipse
import sys
import os
import cv2
from copy import deepcopy
from commonFunctions import createFolder

class exportToUNet:
    categoryBackground = int(0)
    categoryOrganoid = int(255)
    categoryBorder = int(255/2.0)
    """
        This is the reversed rgb color for rgb image sent to be filled with
        export().
    """
    rgbFill = (0,255,255)
    
    def __init__(self):
        pass
    
    """
        Exports the shapes to catagorized images (where the shapes are filled
        with exportToUNet.categoryOrganoid, the border part
        is exportToUNet.categoryBorder and the rest is exportToUNet.categoryBackground).
    
        img - if not None, it will be filled with exportToUNet.rgbFill
                (reversed rgb color).
        shapes - contains the points that make up the shape which is the INTERNAL
                border of the organoid.
        borders - contains the points that make up the shape which is the EXTERNAL
                border of the organoid.
        frameWidth - the width of a frame.
        frameHeight - the height of a frame.
        outFilepath - if not None, the function will write the classification
                data to this file.
                
        Returns:
            The filled frames with the categories: background, organoid, border.
    """
    def export(self, frameCtrl, shapes, borders, frameWidth, frameHeight, outputDir):
        testImageCount = 0#100, DUBUG
        img = None
        
        if len(shapes)==0:
            return
        
        print('   Creating output folders...')
        createFolder(outputDir + 'image/')
        createFolder(outputDir + 'label/')
        print('   Done!')
        
        """
            Some xy have no shapes in them, ignore those.
            We only want to record the xy with shapes in them.
        """
        xyList = []
        
        for xy in range(len(shapes)):
            if len(shapes[xy])==0:
                continue
            
            flagEmptyXY = True
            for t in range(len(shapes[xy])):
                if len(shapes[xy][t])>0:
                    flagEmptyXY = False
                    break
            
            if not flagEmptyXY:
                xyList.append(xy)
        xyList = np.array(xyList)
        
        xyCount = len(xyList)
        frameCount = len(shapes[0])
        
        """
            frames[xy,t]
        """
        frames = np.full(shape=(xyCount, frameCount, frameHeight, frameWidth),
                         fill_value = exportToUNet.categoryBackground,
                         dtype = np.uint8)
        #originalImages = np.full(shape=(xyCount, frameCount, frameHeight, frameWidth),
        #                 fill_value = exportToUNet.categoryBackground,
        #                 dtype = np.uint8)
        
        """
            Draw all the (external) borders
        """
        print('   Exporting borders...')
        testBorderCount = 0
        if borders is not None:
            for xy in range(xyCount):
                print('      xy = '+np.str(xyList[xy]+1))
                for t in range(frameCount):
                    img = None
                    if testBorderCount<testImageCount:
                        flagShapeFound = False
                        for shapeID in range(len(borders[xyList[xy]][t])):
                            points = borders[xyList[xy]][t][shapeID]
                            shapeType = self.__getShapeType(points)
                            
                            if shapeType!='points':
                                flagShapeFound = True
                                break
                            
                        if flagShapeFound:
                            img = deepcopy(frameCtrl.getFrame(xyList[xy], t))
                            img0 = deepcopy(img)
                    
                    for shapeID in range(len(borders[xyList[xy]][t])):                        
                        points = borders[xyList[xy]][t][shapeID]
                        shapeType = self.__getShapeType(points)
                        
                        if shapeType=='circle':
                            center, radius = self.__fitCircle(points)
                            self.__fillCircle(frames[xy,t],
                                              center, radius,
                                              fill_value=exportToUNet.categoryBorder)
                            if img is not None:
                                self.__fillCircle(img,
                                                  center, radius,
                                                  fill_value=exportToUNet.categoryBorder)
                        elif shapeType=='ellipse':
                            center, radius, angle = self.__fitEllipse(points)
                            self.__fillEllipse(frames[xy,t],
                                              center, radius, angle,
                                              fill_value=exportToUNet.categoryBorder)
                            if img is not None:
                                self.__fillEllipse(img,
                                              center, radius, angle,
                                              fill_value=exportToUNet.categoryBorder)
                        elif shapeType=='polygon':
                            self.__fillPolygon(frames[xy,t],
                                               points,
                                               fill_value=exportToUNet.categoryBorder)
                            if img is not None:
                                self.__fillPolygon(img,
                                               points,
                                               fill_value=exportToUNet.categoryBorder)
                        else:
                            #print('   exportToUNet: border type not recognized!')
                            #print('   skipping shape...')
                            # You will have many empty borders
                            pass
                        
                        if img is not None and flagShapeFound:
                            cv2.imwrite('e:/test_images/border_img['+np.str(testBorderCount)+']_0.png', img0)
                            cv2.imwrite('e:/test_images/border_img['+np.str(testBorderCount)+']_1.png', img)
                            testBorderCount += 1
        print('      All borders done!')
        
        """
            Draw all the organoids
            
            This overwrites the internal part of the shape drawn by the borders
            code, which is what we want.
        """
        print('   Exporting shapes...')
        testShapeCount = 0
        count = 0
        for xy in range(xyCount):
            print('      xy = '+np.str(xyList[xy]+1))
            for t in range(frameCount):
                img = None
                if testShapeCount<testImageCount:
                    flagShapeFound = False
                    for shapeID in range(len(shapes[xyList[xy]][t])):                    
                        points = shapes[xyList[xy]][t][shapeID]
                        shapeType = self.__getShapeType(points)
                        if shapeType!='points':
                            flagShapeFound = True
                            break
                        
                    if flagShapeFound:
                        img = deepcopy(frameCtrl.getFrame(xyList[xy], t))
                        img0 = deepcopy(img)
                
                flagShapeFound = False
                frame = np.full((frameHeight, frameWidth),
                                exportToUNet.categoryBackground,
                                dtype=np.uint8)
                for shapeID in range(len(shapes[xyList[xy]][t])):                    
                    points = shapes[xyList[xy]][t][shapeID]
                    shapeType = self.__getShapeType(points)
                    
                    if shapeType!='points':
                        flagShapeFound = True                
                    
                    if shapeType=='circle':
                        center, radius = self.__fitCircle(points)
                        self.__fillCircle(frame,
                                          center, radius,
                                          fill_value=exportToUNet.categoryOrganoid)
                        if img is not None:
                            self.__fillCircle(img,
                                              center, radius,
                                              fill_value=exportToUNet.categoryOrganoid)
                    elif shapeType=='ellipse':
                        center, radius, angle = self.__fitEllipse(points)
                        self.__fillEllipse(frame,
                                          center, radius, angle,
                                          fill_value=exportToUNet.categoryOrganoid)
                        if img is not None:
                            self.__fillEllipse(img,
                                          center, radius, angle,
                                          fill_value=exportToUNet.categoryOrganoid)
                    elif shapeType=='polygon':
                        self.__fillPolygon(frame,
                                           points,
                                           fill_value=exportToUNet.categoryOrganoid)
                        if img is not None:
                            self.__fillPolygon(img,
                                           points,
                                           fill_value=exportToUNet.categoryOrganoid)
                    else:
                        print('   exportToUNet: shape type not recognized!')
                        print('   skipping shape...')
                        
                if img is not None and flagShapeFound:
                    cv2.imwrite('e:/test_images/shape_img['+np.str(testShapeCount)+']_0.png', img0)
                    cv2.imwrite('e:/test_images/shape_img['+np.str(testShapeCount)+']_1.png', img)
                    testShapeCount += 1
                    
                """
                    Save the original image & mask
                """
                if flagShapeFound:
                    originalImage = frameCtrl.getFrame(xyList[xy], t)
                    maskImage = frame
                    cv2.imwrite(outputDir + 'image/'+np.str(count)+'.png', originalImage)
                    cv2.imwrite(outputDir + 'label/'+np.str(count)+'.png', maskImage)
                    count += 1
        print('      All shapes done!')
        
        #if outFilepath is not None:
        #    print('   Saving to output file...')
        #    np.save(outFilepath, frames)
        #    print('      Done!')
        
        #print('  All done!')
        return frames
    
    def __getShapeType(self, points):
        if len(points)<3:
            return 'points'
        elif len(points)<5:
            return 'circle'
        elif len(points)<9:
            return 'ellipse'
        else:
            return 'polygon'
    
    def __fitCircle(self, points):
        return fitCircle(points)
    
    def __fillCircle(self, img, center, radius, fill_value):
        """
            - You need to swap:
                x <-> y
        """
        center = tuple(np.array(center, dtype=int)[::-1])
        radius = np.int(radius)
        if len(img.shape)==3 and img.shape[2]==3:
            cv2.circle(img, center, radius, exportToUNet.rgbFill, cv2.FILLED, 0, 0)
        else:
            cv2.circle(img, center, radius, fill_value, cv2.FILLED, 0, 0)
    
    def __fitEllipse(self, points):
        return fitEllipse(points)
    
    def __fillEllipse(self, img, center, size, angle, fill_value):
        """
            - You need to swap:
                x <-> y
            - We are sending HALF the size, with (x,y) swapped
            - The angle is rotated by 90 degrees due to x,y swap
        """
        center = tuple(np.array(center, dtype=int)[::-1])
        size = tuple(np.array(size, dtype=int)[::-1]/2)
        angle -= 90.0
        if len(img.shape)==3 and img.shape[2]==3:
            cv2.ellipse(img, center, size, angle, 0.0, 360.0,
                        exportToUNet.rgbFill,
                        cv2.FILLED, 0, 0)
        else:
            cv2.ellipse(img, center, size, angle, 0.0, 360.0,
                        fill_value,
                        cv2.FILLED, 0, 0)

    def __fillPolygon(self, img, points, fill_value):
        """
            - You need to swap:
                x <-> y
        """
        points = np.array(points, dtype=int)
        for i in range(len(points)):
            points[i] = points[i][::-1]
        
        if len(img.shape)==3 and img.shape[2]==3:
            cv2.fillPoly(img, [points], exportToUNet.rgbFill)
        else:
            cv2.fillPoly(img, [points], fill_value)