# -*- coding: utf-8 -*-
"""
Created on Thu Jun 07 16:32:39 2018

@author: Edward
"""
from __future__ import print_function
import numpy as np

#import h5py

#np.load('shapes.backup.npy')
#h5py.File('shapes.backup.npy','r')

data = np.load('shapes.backup.npy').item()
dataShapes = data['shapes']

activeXY = []
activeXYFrames = []
for xy in range(dataShapes.shape[0]):
    if np.any(dataShapes[xy]>0):
        activeXY.append(xy)
        activeFrames = 0
        for t in range(len(dataShapes[xy])):
            if len(dataShapes[xy][t])>0:
                activeFrames += 1
        activeXYFrames.append(activeFrames)
activeXY = np.unique(activeXY)

print('activeXY: ',activeXY)
print('activeXYFrames: ',activeXYFrames)