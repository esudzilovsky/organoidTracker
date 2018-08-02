# -*- coding: utf-8 -*-
"""
Created on Sat Jun 09 12:49:42 2018

@author: Edward
"""

import cv2
img = cv2.imread('apple-drawing.jpg') # load a dummy image
while(1):
    cv2.imshow('img',img)
    k = cv2.waitKey(33)
    if k==27:    # Esc key to stop
        break
    elif k==-1:  # normally -1 returned,so don't print it
        continue
    elif (k&0xFF == ord('q')) or (k&0xFF == ord('Q')):
        break
    elif k==6:
        print('CTRL+f')
    else:
        print k # else print its value
cv2.destroyAllWindows()

# '1' == 49
# '2' == 50
# CTRL+x == 24
# CTRL+y == 25
# <enter> == 13
# CTRL+ENTER == 10