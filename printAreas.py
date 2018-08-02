# -*- coding: utf-8 -*-
"""
Created on Sat May 26 20:11:47 2018

@author: Edward
"""

import numpy as np

areas = np.load('D:/2018122_MIS_SOK015.nd2_tracking/shapesArea.npy')

"""
    Find active XY
"""
activeXY = -1
numActiveXY = 0
for xy in range(areas.shape[0]):
    if np.any(areas[xy]>0):
        activeXY = xy
        numActiveXY += 1
if numActiveXY==1:
    print('   DEBUG: a single active xy found ('+np.str(activeXY)+')... setting to it...')

    print('   areas[xy] = ',areas[activeXY])