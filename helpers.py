import numpy as np
import copy
import pickle
import cv2
import time
import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
#from mpl_toolkits.mplot3d import Axes3D


#point annotation object
class Point(object):
	def __init__(self, x, y, colorIdx=0, size=3):
		self.colorIdx = colorIdx
		color = getColor(colorIdx)
		# These points are generated using getRelCoords, meaning
		# that x and y are measured as fractions of the whole image from
		# the upper left corner (0, 0) of the image.
		self.x = x
		self.y = y
	 
		self.color = color
		self.size = size
	
	def __repr__(self):
		return f"X {self.x} Y {self.y} S {self.size}"

	def __add__(self, other):
		return Point(self.x+other.x, self.y+other.y)
	
	def __sub__(self, other):
		return Point(self.x-other.x, self.y-other.y)
	
	def __mul__(self, scalar):
		return Point(self.x*scalar, self.y*scalar)

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

	def show(self, arr, img_shape, size, node, offset, scale):
		x0, y0 = offset
		if node:
			size *= 2
		#draws point to copy of the current frame
		local_x = int(self.x * img_shape[1]) - y0 
		local_y = int(self.y * img_shape[0]) - x0
		cv2.circle(arr, (local_x, local_y), size, self.color, -1)
	
	def updateColor(self, colorIdx):
		self.colorIdx = colorIdx
		self.color = getColor(colorIdx)




def getColor(colorIdx):
	colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
	return colors[colorIdx]



def adjust_color(image, shadows, midtones, highlights):
	# Normalize input values to a range between 0 and 1
	shadows = (shadows-50) / 50
	midtones = (midtones-50) / 50
	highlights = (highlights-50) / 50

	# Convert the image to a floating-point format
	image_float = image.astype(np.float32) / 255.0

	# Adjust shadows
	image_float = np.where(image_float < 0.5, image_float * (1 + shadows), image_float)

	# Adjust midtones (gamma correction)
	image_float = np.power(image_float, 1 / (1 + midtones))

	# Adjust highlights
	image_float = np.where(image_float > 0.5, image_float * (1 - highlights) + highlights, image_float)

	# Clip the values to the range [0, 1] and convert back to the original data type
	adjusted_image = np.clip(image_float * 255, 0, 255).astype(np.uint8)

	return adjusted_image


def interpolatePoints(points, imShape):
	#use linear interpolation to interpolate between points in the annotation list
	pixels = [[i.x*imShape[1], i.y*imShape[0]] for i in points]
	interp = []
	for i in range(len(pixels)-1):
		#find the distance between the two points
		dist = np.sqrt((pixels[i+1][0]-pixels[i][0])**2 + (pixels[i+1][1]-pixels[i][1])**2)
		#find the number of pixels to interpolate between them
		n = int(dist)#TODO
		if n == 0:
			continue
		#find the step size
		step = 1/n
		#interpolate between the two pixels
		for j in np.arange(0,n,1):
			x = pixels[i][0] + (pixels[i+1][0]-pixels[i][0])*j*step
			y = pixels[i][1] + (pixels[i+1][1]-pixels[i][1])*j*step
			interp.append(Point(x/imShape[1], y/imShape[0],0,2))
	return interp


def getImFrameCoords(app, pos):
	"""Returns the coordinates of the mouse reported as a fraction
	of the way through the image frame.
	"""
	pos = getUnscaledRelCoords(app, pos)
	image_rect = app.label.pixmap().rect()
	x = pos.x() / image_rect.width()
	y = pos.y() / image_rect.height()
	return x,y

#get the coordinates of the mouse relative to the full image
def getRelCoords(app, pos):
	"""Returns the coordinates of the mouse reported as a fraction
	of the way through the full image.

	Note that the full image may not be currently displayed, so we have
	to adjust the location appropriately.
	"""
	pos = getUnscaledRelCoords(app, pos)
	image_rect = app.label.pixmap().rect()
	x = pos.x()*app.image.scale+app.image.offset[1]/app.pixelSize1
	y = pos.y()*app.image.scale+app.image.offset[0]/app.pixelSize0
	x /= image_rect.width()
	y /= image_rect.height()
	return x,y


def getUnscaledRelCoords(app, pos):
	"""Takes the mouse position and returns the x, y coordinates represented
	as the pixel distance from the upper left corner of the image.
	"""
	label_pos = app.label.pos()
	image_rect = app.label.pixmap().rect()
	# image_pos here is the pixel position of the upper left corner of the image
	# inside the QT application
	image_pos = QPoint(
		int(label_pos.x() + (app.label.width() - image_rect.width()) / 2),
		int(label_pos.y() + (app.label.height() - image_rect.height()) / 2),
	)
	#get pos relative to image
	pos = pos - image_pos
	return pos


#get pixel coordinates from relative coordinates
def getPixelCoords(imShape, x, y):
	x = int(x*imShape[1])
	y = int(y*imShape[0])
	return x,y
	

def autoSave(app, file_name=None):
	if file_name == None:
		file_name = app.sessionId
	#save annotations to file
	with open(f"{file_name}", 'wb') as f:
		pickle.dump(app.image.annotations, f)
		pickle.dump(app.image.interpolated, f)
		pickle.dump(app.image.imshape, f)
	#save annotations to vcp file
	# TODO: resolve volpkg issues
	# app.volpkg.saveVCPS(app.sessionId0, app.image.interpolated, app.image.imshape)




def plot3Dmesh(points, voxel_data, offset=(0,0,0)):
	points -= np.array(offset)
	# Perform Delaunay triangulation
	tri = Delaunay(points)

	# Create a list to store the colors of each face
	face_colors = []

	# Iterate over the triangles and compute the average voxel value
	for simplex in tri.simplices:
		avg_voxel_value = np.mean([voxel_data[tuple(point)] for point in points[simplex]])
		face_colors.append(avg_voxel_value)

	# Normalize face_colors to be between 0 and 1
	face_colors = (face_colors - np.min(face_colors)) / (np.max(face_colors) - np.min(face_colors))

	# Create a colormap
	cmap = plt.cm.get_cmap("gray")


	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	#set title
	ax.set_title("3D Mesh")

	# Create a collection of triangles with the corresponding colors
	trisurf = ax.plot_trisurf(points[:, 0], points[:, 1], points[:, 2], triangles=tri.simplices)

	# Set the facecolors of the trisurf object
	trisurf.set_facecolors(cmap(face_colors))

	plt.show()