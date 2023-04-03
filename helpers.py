import numpy as np
import copy
import pickle
import cv2
import time

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


#TODO: figure out step size generally (including non square images)

#point annotation object
class Point(object):
    def __init__(self, x, y, colorIdx=0, size=3):
        self.colorIdx = colorIdx
        color = getColor(colorIdx)
        self.x = x
        self.y = y
     
        self.color = color
        self.size = size

    def show(self, arr, size=3):
        #draws point to copy of the current frame
        x = int(self.x*arr.shape[0])
        y = int(self.y*arr.shape[1])
        cv2.circle(arr, (x,y), size, self.color, -1)
    
    def updateColor(self, colorIdx):
        self.colorIdx = colorIdx
        self.color = getColor(colorIdx)

def getColor(colorIdx):
    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
    return colors[colorIdx]


def interpolatePoints(points, imShape):
		#use linear interpolation to interpolate between points in the annotation list
		points = [[i.x, i.y] for i in points]
		interp = []
		for i in range(len(points)-1):
			#find the distance between the two points
			dist = np.sqrt((points[i+1][0]-points[i][0])**2 + (points[i+1][1]-points[i][1])**2)
			#find the number of points to interpolate between them
			n = int(dist*imShape[0])#TODO
			if n == 0:
				continue
			#find the step size
			step = 1/n
			#interpolate between the two points
			for j in np.arange(0,n,3):
				x = points[i][0] + (points[i+1][0]-points[i][0])*j*step
				y = points[i][1] + (points[i+1][1]-points[i][1])*j*step
				interp.append(Point(x, y, 0,2))
		return interp

    
def getRelCoords(app, pos):
    label_pos = app.label.pos()
    image_rect = app.label.pixmap().rect()
    image_pos = QPoint(int(label_pos.x() + (app.label.width() - image_rect.width()) / 2),int(label_pos.y() + (app.label.height() - image_rect.height()) / 2))
    print(f"image pos: {image_pos.x()}, {image_pos.y()}")
    #get pos relative to image 
    pos = pos - image_pos

    x = pos.x()*app.image.scale+app.image.offset[1]/app.pixelSize1
    y = pos.y()*app.image.scale+app.image.offset[0]/app.pixelSize0
    x /= image_rect.height()
    y /= image_rect.width()
    return x,y