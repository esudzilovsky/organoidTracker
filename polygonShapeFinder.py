# -*- coding: utf-8 -*-
"""
Created on Mon May 07 19:22:31 2018

@author: Edward
"""

from operator import itemgetter
import numpy as np
from copy import deepcopy
"""
import random
import matplotlib
import matplotlib.pyplot
"""

"""
    This class takes the points of a non intersecting polygon and sorts them out
    so that the lines drawn are in the right order and don't intersect.
"""
class PolygonShapeFinder:
    def __init__(self, array):#, min_rand_coord = None, max_rand_coord = None, points_num = None):        
        self.array = array
        self.points_num = len(array)
        #self.min_rand_coord = min_rand_coord 
        #self.max_rand_coord = max_rand_coord
        #self.points_num = points_num

    """
    def generate_random_points(self):
        random_coords_list = []
        for x in range(self.points_num):
            coords_tuple = (random.randint(self.min_rand_coord, self.max_rand_coord),
                            random.randint(self.min_rand_coord, self.max_rand_coord))
            random_coords_list.append(coords_tuple)
        self.array = random_coords_list
        return random_coords_list
    """

    def close_line_to_polygon(self):
        self.array = self.array.tolist()
        a = self.array[0]
        b = self.array[len(self.array)-1]
        if np.all(a == b):
            pass
        else:
            self.array.append(a)    

    def find_leftmost_point(self):
        leftmost_point = None
        leftmost_x = None
        for point in self.array:
            x = point[0]
            if leftmost_x == None or x < leftmost_x:
                leftmost_x = x
                leftmost_point = point
        return leftmost_point

    def find_rightmost_point(self):
        rightmost_point = None
        rightmost_x = None
        for point in self.array:
            x = point[0]
            if rightmost_x == None or x > rightmost_x:
                rightmost_x = x
                rightmost_point = point
        return rightmost_point

    def is_point_above_the_line(self, point, line_points):
        """return 1 if point is above the line
           return -1 if point is below the line
           return  0 if point is lays on the line"""
        px, py = point
        P1, P2 = line_points
        P1x, P1y = P1[0], P1[1]
        P2x, P2y = P2[0], P2[1]
        array = np.array([
            [P1x - px, P1y - py],
            [P2x - px, P2y - py],
            ])
        det = np.linalg.det(array)
        sign = np.sign(det)
        return sign

    def sort_array_into_A_B_C(self, line_points):
        [(x_lm, y_lm), (x_rm, y_rm)] = line_points
        A_array, B_array, C_array = [], [], []
        for point in self.array:
            x, y = point
            sing = self.is_point_above_the_line( (x, y), line_points)
            if sing == 0:
                C_array.append(point)
            elif sing == -1:
                A_array.append(point)
            elif sing == 1:
                B_array.append(point)
        return A_array, B_array, C_array

    def sort_and_merge_A_B_C_arrays(self, A_array, B_array, C_array):
        if len(A_array)==0:
            A_C_array = deepcopy(C_array)
        elif len(C_array)==0:
            A_C_array = deepcopy(A_array)
        else:
            A_C_array = np.concatenate([A_array, C_array]).tolist()#[*A_array, *C_array]
        A_C_array.sort(key=itemgetter(0))
        B_array.sort(key=itemgetter(0), reverse=True)
        if len(A_C_array)==0:
            merged_arrays = deepcopy(B_array)
        elif len(B_array)==0:
            merged_arrays = deepcopy(A_C_array)
        else:
            merged_arrays = np.concatenate([A_C_array, B_array])
        self.array = merged_arrays

    """
    def show_image(self, array, line_points, A_array, B_array, C_array):
        [(x_lm, y_lm), (x_rm, y_rm)] = line_points        
        x = [x[0] for x in array]
        y = [y[1] for y in array]
        Ax = [x[0] for x in A_array]
        Ay = [y[1] for y in A_array]
        Bx = [x[0] for x in B_array]
        By = [y[1] for y in B_array]
        Cx = [x[0] for x in C_array]
        Cy = [y[1] for y in C_array]          
        matplotlib.pyplot.plot(Ax, Ay, 'o', c='orange') # below the line
        matplotlib.pyplot.plot(Bx, By, 'o', c='blue') # above the line
        matplotlib.pyplot.plot(Cx, Cy, 'o', c='black') # on the line
        matplotlib.pyplot.plot(x_lm, y_lm, 'o', c='green') # leftmost point
        matplotlib.pyplot.plot(x_rm, y_rm, 'o', c='red') # rightmost point
        x_plot = matplotlib.pyplot.plot([x_lm, x_rm], [y_lm, y_rm], linestyle=':', color='black', linewidth=0.5) # polygon's division line
        x_plot = matplotlib.pyplot.plot(x, y, color='black', linewidth=1) # connect points by line in order of apperiance        
        matplotlib.pyplot.show()
    """

    def getSortedPolygon(self):#, plot = False):
        """
        'First output is random polygon coordinates array (other stuff for ploting)'
        print(self.array)
        if self.array == None:
            if not all(
                [isinstance(min_rand_coord, int),
                 isinstance(max_rand_coord, int),
                 isinstance(points_num, int),]
                ):
                print('Error! Values must be "integer" type:', 'min_rand_coord =',min_rand_coord, ', max_rand_coord =',max_rand_coord, ', points_num =',points_num)
            else:                
                self.array = self.generate_random_points()            

        print(self.array)
        """
        x_lm, y_lm = self.find_leftmost_point()
        x_rm, y_rm = self.find_rightmost_point()
        line_points = [(x_lm, y_lm), (x_rm, y_rm)]

        A_array, B_array, C_array = self.sort_array_into_A_B_C(line_points)
        self.sort_and_merge_A_B_C_arrays(A_array, B_array, C_array)
        self.close_line_to_polygon()
        return self.array
        """
        if plot:
            self.show_image(self.array, line_points, A_array, B_array, C_array)
        return self.array
        """