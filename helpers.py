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
	
	def __add__(self, other):
		return Point(self.x+other.x, self.y+other.y)
	
	def __sub__(self, other):
		return Point(self.x-other.x, self.y-other.y)
	
	def __mul__(self, scalar):
		return Point(self.x*scalar, self.y*scalar)

	#subscripting
	def __getitem__(self, key):
		if key == 0:
			return self.x
		elif key == 1:
			return self.y
		else:
			raise IndexError("Point index out of range")
	
	def __setitem__(self, key, value):
		if key == 0:
			self.x = value
		elif key == 1:
			self.y = value
		else:
			raise IndexError("Point index out of range")


	def show(self, arr, size, node):
		if node:
			size *= 2
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
	pos = getUnscaledRelCoords(app, pos)
	image_rect = app.label.pixmap().rect()
	x = pos.x()*app.image.scale+app.image.offset[1]/app.pixelSize1
	y = pos.y()*app.image.scale+app.image.offset[0]/app.pixelSize0
	x /= image_rect.height()
	y /= image_rect.width()
	return x,y

def getUnscaledRelCoords(app, pos):
	label_pos = app.label.pos()
	image_rect = app.label.pixmap().rect()
	image_pos = QPoint(int(label_pos.x() + (app.label.width() - image_rect.width()) / 2),int(label_pos.y() + (app.label.height() - image_rect.height()) / 2))
	#get pos relative to image 
	pos = pos - image_pos
	return pos

def autoSave(app):
	with open(app.sessionId, 'wb') as f:
		pickle.dump(app.image.annotations, f)
		pickle.dump(app.image.interpolated, f)
		pickle.dump(app.image.img.shape, f)