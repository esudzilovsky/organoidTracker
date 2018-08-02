# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 15:58:07 2018

@author: Edward
"""

import numpy as np
import cv2
from mouseControl import MouseControl
from pointsManager import PointsManager
from circleManager import CircleManager, SingleCircleDrawingManager
import time

circlesMgr = CircleManager()
circleDrawingMgr = SingleCircleDrawingManager()
shapeMgr = PointsManager(1, 0)
mouseCtrl = MouseControl(circlesMgr, circleDrawingMgr, shapeMgr)

#cv2.namedWindow('frame');
#cv2.setMouseCallback('frame', mouseCtrl.callback);

start = time.time()
im = cv2.imread('e:\\1.tiff')

shape = np.array(im.shape)
factor = 0.5
shape = tuple(np.array(0.5*shape,dtype=int))

im2 = cv2.resize(im, (int(shape[0]), int(shape[1])), interpolation=cv2.INTER_CUBIC)

#cv2.imshow("frame", im2)
end = time.time()
elapsed = end-start
print('Elapsed :'+np.str(np.round(elapsed,3))+'s')