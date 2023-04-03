#image object that handles zooming, panning, and annotating (how to handle z-integration?)
import numpy as np
import cv2
from PyQt5.QtGui import QPixmap, QImage
import copy
from helpers import Point
from PIL import Image
#ModuleNotFoundError: No module named 'PIL'
#pip3 install pillow

class mImage(object):
	def __init__(self, img, _frame_count, display_size=800, pixelSize=1):
		self.img = cv2.imread(img)
		self.pixelSize = pixelSize
		self.display_width = display_size
		self.display_height = int(display_size*self.img.shape[1]/self.img.shape[0])
		#print(self.display_height, self.display_width)
		self.scale = 1
		self.offset = np.array([0.0,0.0])
		self.annotations = [[] for i in range(_frame_count)] #list of annotations of type mAnnotation
		self.interpolated = [[] for i in range(_frame_count)]
		self.annotationRadius = 3

		self.contrast = 3


	def setImg(self, img):
		self.img = cv2.imread(img)

	def zoom(self, factor):
		print("zooming")
		self.scale *= factor
		if self.scale < 0.01:
			self.scale = 0.01
		if self.scale > 1:
			self.scale = 1
		print(self.scale)

	def pan(self, doffset):
		#get all four corners of the image
		x0 = int(self.offset[0])
		y0 = int(self.offset[1])
		x1 = int(self.img.shape[0]*self.scale)
		y1 = int(self.img.shape[1]*self.scale)
		if x0 + doffset[0] < 0:
			doffset[0] = -x0
		if y0 + doffset[1] < 0:
			doffset[1] = -y0
		if x0 + doffset[0] + x1 > self.img.shape[0]:
			doffset[0] = self.img.shape[0] - x0 - x1
		if y0 + doffset[1] + y1 > self.img.shape[1]:
			doffset[1] = self.img.shape[1] - y0 - y1
		self.offset += doffset*self.scale
	
	def addAnnotation(self, annotation):
		pass #need to think more about this

	def removeAnnotation(self, annotation):
		pass

	def showAnnotations(self, img, frame_index):
		for an in self.annotations[frame_index]:
			an.show(img, self.annotationRadius)
		for an in self.interpolated[frame_index]:
			#print("showing interpolated")
			an.show(img, self.annotationRadius)
	

	def get2DImage(self):
		colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
		#here's how we'll unwrap the annotations
		#first we'll find the bounding box of the annotations which is len(annotations), max([len(i) for i in interpolated])
		#then we'll create a new image of that size
		#then we'll find the "center" of each slices annotations, by finding the point with min distance from true center (i.e. center of middle slice)
		#then for each slice populate the new image with the annotations to the left and right of the center
		#remove all empty slices
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
				for jindex, j in enumerate(interpolated[i]):
					im[i, W - (centerIndex-jindex)] = colors[interpolated[i][jindex].colorIdx]
			
		return im

				




	def reset(self):
		self.scale = 1
		self.offset = np.array([0.0,0.0])

	def getImg(self, frame_index, show_annotations=True):
		#return the image with the current zoom and pan applied
		x0 = int(self.offset[0])
		y0 = int(self.offset[1])
		img = self.getProcImg()

		if show_annotations:
			self.showAnnotations(img, frame_index)
		#roll the image to account for the offset
		img = np.roll(img, -x0, axis=0)
		img = np.roll(img, -y0, axis=1)
		x1 = int(img.shape[0]*self.scale)
		y1 = int(img.shape[1]*self.scale)
		#resize the image by interpolation
		img = cv2.resize(img[:x1, :y1], (self.display_height, self.display_width))
		#CONVERT to pixmap
		#print(type(img))
		data = img
		bytesperline = 3 * data.shape[1]
		qimg = QImage(data, data.shape[1], data.shape[0], bytesperline, QImage.Format_RGB888)
		pixmap = QPixmap.fromImage(qimg)
		#TypeError: fromImage(image: QImage, flags: Union[Qt.ImageConversionFlags, Qt.ImageConversionFlag] = Qt.AutoColor): argument 1 has unexpected type 'numpy.ndarray'
		#
		return pixmap


	def getProcImg(self, filename=None):
		if filename is None:
			img = copy.deepcopy(self.img)
		else:
			img = cv2.imread(filename)
	
		#invert the image
		img = cv2.bitwise_not(img)
		#apply contrast filter
		img = cv2.convertScaleAbs(img, alpha=self.contrast/5,beta=100)

		img = cv2.bitwise_not(img)
		#apply brightness threshold
		#img = np.where(img > 20, 255, 0)
		img = cv2.convertScaleAbs(img)
		#do the above with cv2
		# img = cv2.threshold(img, 20, 255, cv2.THRESH_BINARY)
		# img = img[1]
		

		return img
	


