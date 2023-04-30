#image object that handles zooming, panning, and annotating (how to handle z-integration?)
import numpy as np
import cv2
from PyQt5.QtGui import QPixmap, QImage

class mImage(object):
	def __init__(self, frame_count, img_loader, display_size=800):
		self.img_loader = img_loader
		# N.B. this is z, x, y
		self.shape = self.img_loader.shape
		self.imshape = self.shape[1:]
		self.loaded_shape = None
		# This will hold the pixmap once loaded
		self.img = None
	
		maxDim = np.argmax(self.imshape)
		if maxDim == 0:
			self.display_width = display_size
			self.display_height = int(display_size*self.imshape[1]/self.imshape[0])
		else:
			self.display_height = display_size
			self.display_width = int(display_size*self.imshape[0]/self.imshape[1])

		# Defines the zoom level and the (X,Y) offset of where to start drawing.
		self.scale = 1
		self.offset = np.array([0.0,0.0])

		self.annotations = [[] for i in range(frame_count)] #list of annotations of type mAnnotation
		self.interpolated = [[] for i in range(frame_count)]
		self.annotationRadius = 3

		self.contrast = 3

		self.invert = False

	###########################################################################
	# Functions for controlling the zoom and pan of the image
	###########################################################################

	def reset(self):
		self.scale = 1
		self.offset = np.array([0.0,0.0])

	def zoom(self, factor):
		self.scale *= factor
		if self.scale < 0.01:
			self.scale = 0.01
		if self.scale > 1:
			self.scale = 1

	def pan(self, doffset):
		x0 = int(self.offset[0])
		y0 = int(self.offset[1])
		x1 = int(self.imshape[0]*self.scale)
		y1 = int(self.imshape[1]*self.scale)
		if x0 + doffset[0] < 0:
			doffset[0] = -x0
		if y0 + doffset[1] < 0:
			doffset[1] = -y0
		if x0 + doffset[0] + x1 > self.imshape[0]:
			doffset[0] = self.imshape[0] - x0 - x1
		if y0 + doffset[1] + y1 > self.imshape[1]:
			doffset[1] = self.imshape[1] - y0 - y1
		self.offset += doffset*self.scale
		
	
	###########################################################################

	def getImg(self, frame_index, show_annotations=True):
		#return the image with the current zoom and pan applied
		x0 = int(self.offset[0])
		y0 = int(self.offset[1])
		x1 = int(self.imshape[0]*self.scale)
		y1 = int(self.imshape[1]*self.scale)
		self.loaded_shape = (x1, y1)
		img = self.img_loader[frame_index, x0:x0+x1, y0:y0+y1]
		
		img = self.normalize_image(img=img)
		if show_annotations:
			for an in self.annotations[frame_index]:
				an.show(img, self.imshape, self.annotationRadius, True, x0, y0, self.scale)
			for an in self.interpolated[frame_index]:
				an.show(img, self.imshape, self.annotationRadius, False, x0, y0, self.scale)
		
		
		#resize the image by interpolation
		img = cv2.resize(img, (self.display_height, self.display_width))
		#convert to pixmap
		qimg = QImage(img, img.shape[1], img.shape[0], QImage.Format_RGB888)
		pixmap = QPixmap.fromImage(qimg)
		self.img = pixmap
		return pixmap

	def normalize_image(self, img=None, index=None):
		if index is not None:
			# We first query for the full slice of data
			img = self.img_loader[0,:,:]
		if self.invert:
			img = cv2.bitwise_not(img)
		# Incoming should be a single array of uint16s.
		# We need to convert to a stacked copy of uint8s to display as RGB.
		if type(img[0,0]) == np.uint16:
			f = (np.iinfo(np.uint16).max / np.iinfo(np.uint8).max)
		else:
			f = 1
		img = cv2.convertScaleAbs(
			(img / f).astype(np.uint8), 
			alpha=self.contrast/5, 
			beta=100
		)
		return np.stack([img, img, img], axis=2)

	def get2DImage(self, app):
		"""Unwraps the active annotations.
		first we'll find the bounding box of the annotations which is len(annotations), 
		max([len(i) for i in interpolated])
		then we'll create a new image of that size
		then we'll find the "center" of each slices annotations, by finding the point 
		with min distance from true center (i.e. center of middle slice)
		then for each slice populate the new image with the annotations to the left and right of the center
		remove all empty slices
		"""
		colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
		interpolated = [i for i in self.interpolated if len(i) > 0]

		H = len(interpolated)
		W = max([len(i) for i in interpolated])
		im = np.zeros((H, W*2, 3))
		cy = H//2

		Center = interpolated[cy][len(interpolated[cy])//2]
		for i in range(len(interpolated)):
			if len(interpolated[i]) > 0:
				#find the center of the slice by finding the point with min distance from true center
				center = interpolated[i][0]
				centerIndex = 0
				for jindex, j in enumerate(interpolated[i]):
					if np.sqrt((j.x-Center.x)**2 + (j.y-Center.y)**2) < np.sqrt((center.x-Center.x)**2 + (center.y-Center.y)**2):
						center = j
						centerIndex = jindex
				#populate the image with the interpolated to the left and right of the center
				n = app.inkRadius
				for jindex, j in enumerate(interpolated[i]):
					if app.unwrapStyle == "Annotate":
						val = colors[interpolated[i][jindex].colorIdx]
					else:
						x,y = interpolated[i][jindex].x, interpolated[i][jindex].y
						x *= self.imshape[0]
						y *= self.imshape[1]
						region = self.img_loader[i, int(y-n):int(y+n), int(x-n):int(x+n)]
						val = np.mean(region, axis=(0,1))
					im[i, W - (centerIndex-jindex)] = val
			
		return im
