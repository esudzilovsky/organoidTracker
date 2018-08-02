# -*- coding: utf-8 -*-
"""
Created on Tue Jul 17 14:14:33 2018

@author: Edward
"""

from __future__ import print_function

import numpy as np
import sys
import copy

DEBUG = False

def equal(x, y):
    if DEBUG:
        print('equal('+np.str(x)+', '+np.str(y)+')')
    
    """
        Are the some kind of list?
    """
    notListCount = 0
    try:
        len(x)
    except TypeError as te:
        notListCount += 1
    try:
        len(y)
    except TypeError as te:
        notListCount += 1
    
    """
        One is some form of list, the other isn't
    """    
    if notListCount==1:
        return False
    
    """
        Both are not lists of some form
    """
    if notListCount==2:
        return (x is y) or (x==y) or np.equal(x,y)
    
    """
        Both are lists of some form
    """
    return all_equal(x, y)
    
    """
        The following fails with one as a list of numpy arrays...
    """
    """
    print('equal x=',x,' y=',y, 'type(x)=',type(x),' type(y)=',type(y))
    if type(x)==set and type(y)==set:
        return x==y
    if type(x)==np.ndarray and type(y)==np.ndarray:
        return np.array_equal(x, y)
    if type(x)==np.ndarray:
        x = x.tolist()
    if type(y)==np.ndarray:
        y = y.tolist()
    if type(x)==list:
        x = set(x)
    if type(y)==list:
        y = set(y)
    if type(x)==dict or type(y)==dict:
        print('Sorry need to add dict comparison functionality!')
        sys.exit()
    return x==y
    """

"""
    flagInternal: are we comparing an internal list or was
    it sent with these (x,y) parameters externally?
"""
def all_equal(x, y, flagInternal=False):
    if DEBUG:
        print('all_equal('+np.str(x)+', '+np.str(y)+')')
    
    """
        Are the some kind of list?
    """
    flagXNotList, flagYNotList = False, False
    try:
        len(x)
    except TypeError as te:
        flagXNotList = True
        if DEBUG:
            print('--- x='+str(x)+' not list')
    try:
        len(y)
    except TypeError as te:
        flagYNotList = True
        if DEBUG:
            print('--- y='+str(y)+' not list')
        
    """
        Both not lists
    """
    if flagXNotList and flagYNotList:
        return equal(x, y)
    
    """
        First not list, second is a type of list
    """
    if flagXNotList:
        if len(x)==0 and flagInternal:
            return False
        
        for i in range(len(y)):
            if not all_equal(x, y[i], flagInternal=True):
                return False
        return True
    
    """
        Second not list, first it type of list
    """
    if flagYNotList:
        if len(x)==0 and flagInternal:
            return False
        
        for i in range(len(x)):
            if not all_equal(x[i], y, flagInternal=True):
                return False
        return True
    
    """
        They are both some form of list
    """
    
    if len(x)!=len(y):
        return False
    
    """
        If they are lists, test recursively
    """
    for i in range(len(x)):
        if not all_equal(x[i], y[i], flagInternal=True):
            return False
    return True

"""
    flagInternal: are we comparing an internal list or was
    it sent with these (x,y) parameters externally?
"""
def all_not_equal(x, y, flagInternal=False):
    if DEBUG:
        print('all_equal('+np.str(x)+', '+np.str(y)+')')
    
    """
        Are the some kind of list?
    """
    flagXNotList, flagYNotList = False, False
    try:
        len(x)
    except TypeError as te:
        flagXNotList = True
        if DEBUG:
            print('--- x='+str(x)+' not list')
    try:
        len(y)
    except TypeError as te:
        flagYNotList = True
        if DEBUG:
            print('--- y='+str(y)+' not list')
        
    """
        Both not lists
    """
    if flagXNotList and flagYNotList:
        return not_equal(x, y)
    
    """
        First not list, second is a type of list
    """
    if flagXNotList:
        if len(x)==0 and flagInternal:
            return True
        
        for i in range(len(y)):
            if all_equal(x, y[i], flagInternal=True):
                return False
        return True
    
    """
        Second not list, first it type of list
    """
    if flagYNotList:
        if len(x)==0 and flagInternal:
            return True
        
        for i in range(len(x)):
            if all_equal(x[i], y, flagInternal=True):
                return False
        return True
    
    """
        They are both some form of list
    """
    
    if len(x)!=len(y):
        return True
    
    """
        If they are lists, test recursively
    """
    for i in range(len(x)):
        if all_equal(x[i], y[i], flagInternal=True):
            return False
    return True
    
def any_equal(x, y):
    """
        Are the some kind of list?
    """
    flagXNotList, flagYNotList = False, False
    try:
        len(x)
    except TypeError as te:
        flagXNotList = True
    try:
        len(y)
    except TypeError as te:
        flagYNotList = True
        
    if flagXNotList and flagYNotList:
        return equal(x, y)
    
    if flagXNotList:
        for i in range(len(y)):
            if any_equal(x, y[i]):
                return True
        return False
    
    if flagYNotList:
        for i in range(len(x)):
            if any_equal(x[i], y):
                return True
        return False
    
    """
        They are both some form of list
    """
    
    if len(x)!=len(y):
        return False
    
    """
        If they are lists, test recursively
    """
    for i in range(len(x)):
        if any_equal(x[i], y[i]):
            return True
    return False

def not_equal(x, y):
    return not equal(x,y)

def any_not_equal(x, y):
    return not all_equal(x, y)

    """
        Are the some kind of list?
    """
    flagXNotList, flagYNotList = False, False
    try:
        len(x)
    except TypeError as te:
        flagXNotList = True
    try:
        len(y)
    except TypeError as te:
        flagYNotList = True
        
    if flagXNotList and flagYNotList:
        return equal(x, y)
    
    if flagXNotList:
        for i in range(len(y)):
            if any_not_equal(x, y[i]):
                return True
        return False
    
    if flagYNotList:
        for i in range(len(x)):
            if any_not_equal(x[i], y):
                return True
        return False
    
    """
        They are both some form of list
    """
    
    if len(x)!=len(y):
        return True
    
    """
        If they are lists, test recursively
    """
    for i in range(len(x)):
        if any_not_equal(x[i], y[i]):
            return True
    return False

testCount = 0
def testSuccess(flag):
    global testCount
    if flag:
        print('Test #'+np.str(testCount)+' passed.')
        testCount += 1
    else:
        print('Test #'+np.str(testCount)+' failed.')
        testCount += 1
        sys.exit()
              

if __name__=='__main__':
    """
        Tests
    """
    
    # 0
    testSuccess(equal(None, None))
    
    # 1
    testSuccess(not_equal(None, []))
    
    # 2
    testSuccess(equal([], []))
    
    # 3
    a = []
    b = copy.deepcopy(a)
    testSuccess(equal(a, b))
    
    # 4
    a = [[],[]]
    b = [[],[]]
    testSuccess(equal(a, b))
    
    # 5
    a = [[],[]]
    b = [[],[[]]]
    testSuccess(not_equal(a, b))
    
    # 6
    a = np.array([])
    b = []
    testSuccess(equal(a, b))
    
    # 7
    a = [[0,1],[]]
    b = [[0,1],[1]]
    testSuccess(not_equal(a, b))
    
    # 8
    a = [[0,1],[[0,[4,[]]]]]
    b = [[0,1],[[0,[4,None]]]]
    testSuccess(not_equal(a, b))
    
    # 9
    a = [[0,1],[[0,[4,[]]]]]
    b = [np.array([0,1]),[[0,[4,[]]]]]
    testSuccess(equal(a, b))
    
    # 10
    a = [[0,1],[[0,[np.array([4,6]),np.array([4,6])]]]]
    b = [[0,1],[[0,[np.array([4,6]),np.array([4,6])]]]]
    testSuccess(equal(a, b))
    
    # 11
    a = [5, 5]
    b = 5
    testSuccess(all_equal(a, b))
    
    # 12
    a = [[0,1],[[0,[4,[]]]]]
    b = [[0,1],[[0,[4,[]]]]]
    testSuccess(all_equal(a, b))
    
    # 13
    a = [[0,1],[[0,[4,[]]]]]
    b = [[0,1],[[0,[4,None]]]]
    testSuccess(any_not_equal(a, b))
    
    # 14
    a = np.array([6,6,6.0])
    b = 6
    testSuccess(all_equal(a, b))
    
    # 15
    a = np.array([6,6,3,6.0])
    b = 6
    testSuccess(any_not_equal(a, b))